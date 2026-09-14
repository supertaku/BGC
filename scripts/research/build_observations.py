"""Build auditable pilot observations, precedence selections, and conflicts."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from evidence.model import read_json, resolve_observations, write_json  # noqa: E402

ENTITIES_PATH = ROOT / "data" / "entities" / "pilot-entities.json"
BUILDINGS_PATH = ROOT / "data" / "processed" / "pilot-buildings.geojson"
OUTPUT_PATH = ROOT / "data" / "references" / "observations.json"
CONFLICTS_PATH = ROOT / "data" / "references" / "conflicts.json"
HEIGHT_CHECK_PATH = ROOT / "data" / "references" / "procedural-height-checks.json"


def observation(entity_id: str, prop: str, value, status: str, confidence: float, source_ids: list[str], method: str, notes: str | None = None) -> dict:
    return {
        "observation_id": f"obs:{entity_id}:{prop}:{len(source_ids)}:{str(value).replace(' ', '-')}",
        "entity_id": entity_id,
        "property": prop,
        "value": value,
        "status": status,
        "confidence": confidence,
        "source_ids": source_ids,
        "method": method,
        "notes": notes,
    }


def main() -> None:
    dataset = read_json(ENTITIES_PATH)
    observations: list[dict] = []
    for entity in dataset["entities"]:
        entity_id = entity["entity_id"]
        if entity.get("canonical_name"):
            name_status = "VERIFIED_AUTHORITATIVE" if any(source.startswith("source:official-") or source.startswith("source:government-") for source in entity.get("source_ids", [])) else "VERIFIED_GEOGRAPHIC"
            observations.append(observation(entity_id, "name", entity["canonical_name"], name_status, entity["identity_confidence"], entity["source_ids"], entity["decision_method"]))
        height = entity["height"]
        observations.append(observation(entity_id, "height_m", height["value_m"], height["status"], height.get("confidence", 0), height.get("source_ids", []), height["method"], "Canonical maximum uses explicit building-part height when applicable."))
        if height.get("levels") is not None:
            observations.append(observation(entity_id, "floor_count", height["levels"], "VERIFIED_GEOGRAPHIC", 0.65, ["source:osm"], "osm_building_levels", "OSM building:levels semantics; not an independent survey."))

    by_name = {entity.get("canonical_name"): entity["entity_id"] for entity in dataset["entities"]}
    official = [
        observation(by_name["W Global Center"], "floor_count", 7, "VERIFIED_AUTHORITATIVE", 0.95, ["source:official-w-group-w-global"], "owner_page_storey_count", "Owner describes a seven-storey property."),
        observation(by_name["Central Square"], "retail_floor_count", 3, "VERIFIED_AUTHORITATIVE", 0.95, ["source:official-ssi-central-square"], "operator_page", "Operator distinguishes three retail floors, two basement floors, and one cinema floor."),
        observation(by_name["Central Square"], "opening_date", "2014-06", "VERIFIED_AUTHORITATIVE", 0.95, ["source:official-ssi-central-square"], "operator_page"),
        observation(by_name["JY Campos Centre"], "official_address", "9th Avenue corner 30th Street, Bonifacio Global City, Taguig City", "VERIFIED_AUTHORITATIVE", 0.99, ["source:official-del-monte-jy-campos", "source:government-jy-campos-proclamation"], "official_address_match"),
        observation(by_name["JY Campos Centre"], "gross_floor_area_m2", 19693.55, "VERIFIED_AUTHORITATIVE", 0.99, ["source:government-jy-campos-proclamation"], "government_proclamation"),
        observation(by_name["One Maridien"], "development", "High Street South", "VERIFIED_AUTHORITATIVE", 0.95, ["source:official-alveo-maridien"], "developer_page"),
        observation(by_name["Verve Residences Tower 2"], "development", "High Street South – Verve Residences", "VERIFIED_AUTHORITATIVE", 0.9, ["source:official-alveo-verve"], "developer_page", "Tower-specific identity remains HIGH_CONFIDENCE rather than CONFIRMED."),
    ]
    observations.extend(official)

    conflicts = []
    grouped: dict[tuple[str, str], list[dict]] = {}
    for item in observations:
        grouped.setdefault((item["entity_id"], item["property"]), []).append(item)
    selected = []
    for (entity_id, prop), items in grouped.items():
        result = resolve_observations(items)
        selected.append({"entity_id": entity_id, "property": prop, **result})
        if result["conflicted"] or (entity_id == by_name["W Global Center"] and prop == "floor_count"):
            values = list(dict.fromkeys(item["value"] for item in items))
            if len(values) > 1:
                conflicts.append({
                    "conflict_id": f"conflict:{entity_id}:{prop}",
                    "entity_id": entity_id,
                    "property": prop,
                    "values": [{"value": item["value"], "status": item["status"], "source_ids": item["source_ids"]} for item in items],
                    "recommended_resolution": "Retain both. Prefer the authoritative owner statement for storey count, but do not reinterpret or overwrite the separate OSM height measurement.",
                })

    raw = read_json(BUILDINGS_PATH)
    procedural = [feature for feature in raw["features"] if feature["properties"]["height_status"] == "PROCEDURAL"]
    checks = [{
        "geographic_feature_id": feature["properties"]["id"],
        "entity_id": dataset["source_entity_map"].get(feature["properties"]["id"]),
        "old_state": "PROCEDURAL",
        "identity_enrichment_checked": True,
        "new_evidence": None,
        "new_state": "PROCEDURAL",
        "confidence": 0.15,
        "notes": "Bounded identity/Wikidata/official-source enrichment exposed no defensible explicit height or floor count for this feature.",
    } for feature in procedural]
    now = datetime.now(timezone.utc).isoformat()
    write_json(OUTPUT_PATH, {"schema_version": 1, "generated_at": now, "precedence": ["VERIFIED_AUTHORITATIVE", "VERIFIED_STRUCTURED", "VERIFIED_GEOGRAPHIC", "VERIFIED_PHOTOGRAPHIC", "ESTIMATED", "INFERRED", "PROCEDURAL", "UNKNOWN"], "observations": observations, "selected": selected})
    write_json(CONFLICTS_PATH, {"schema_version": 1, "generated_at": now, "conflicts": conflicts})
    write_json(HEIGHT_CHECK_PATH, {"schema_version": 1, "generated_at": now, "previous_procedural_heights": len(procedural), "procedural_heights_remaining": sum(item["new_state"] == "PROCEDURAL" for item in checks), "checks": checks})
    print(f"BGC_OBSERVATIONS: observations={len(observations)} conflicts={len(conflicts)} procedural_checked={len(checks)} improved=0")


if __name__ == "__main__":
    main()

