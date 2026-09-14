"""Resolve pilot geographic features into persistent project-owned entities."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any

from pyproj import Transformer
from shapely.geometry import mapping, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from evidence.model import normalize_name, read_json, stable_hash, write_json  # noqa: E402


INPUT_PATH = ROOT / "data" / "processed" / "pilot-buildings.geojson"
OUTPUT_PATH = ROOT / "data" / "entities" / "pilot-entities.json"
ALIASES_PATH = ROOT / "data" / "entities" / "aliases.json"
REVIEW_PATH = ROOT / "data" / "review" / "entity-match-review.json"
LOCAL_TO_WGS84 = Transformer.from_crs("EPSG:32651", "EPSG:4326", always_xy=True)

OFFICIAL_MATCHES: dict[str, dict[str, Any]] = {
    "osm:way:145147831": {
        "canonical_name": "W Global Center",
        "source_ids": ["source:official-w-group-w-global", "source:wikidata"],
        "official_url": "https://wgroup.com.ph/projects/w-global-center-3/",
        "status": "CONFIRMED",
        "confidence": 0.99,
        "reason": "Direct OSM Wikidata identifier plus owner page matching 9th Avenue and 30th Street.",
    },
    "osm:way:242294490": {
        "canonical_name": "JY Campos Centre",
        "source_ids": ["source:official-del-monte-jy-campos", "source:government-jy-campos-proclamation"],
        "official_url": "https://www.delmontephil.com/contact",
        "status": "CONFIRMED",
        "confidence": 0.99,
        "reason": "Company and government sources match the named building at 9th Avenue and 30th Street.",
    },
    "osm:way:205968610": {
        "canonical_name": "Central Square",
        "source_ids": ["source:official-ssi-central-square"],
        "official_url": "https://ssilife.com.ph/central-square",
        "status": "CONFIRMED",
        "confidence": 0.97,
        "reason": "Official operator page matches the named property and Bonifacio High Street Central location.",
    },
    "osm:way:1070584577": {
        "canonical_name": "One Maridien",
        "source_ids": ["source:official-alveo-maridien"],
        "official_url": "https://www.alveoland.com.ph/properties/condos/taguig/hss-maridien/",
        "status": "CONFIRMED",
        "confidence": 0.96,
        "reason": "Official developer page name and coordinates match the OSM footprint location.",
    },
    "osm:way:1070584578": {
        "canonical_name": "Verve Residences Tower 2",
        "source_ids": ["source:official-alveo-verve"],
        "official_url": "https://www.alveoland.com.ph/properties/condos/taguig/hss-verve-residences/",
        "status": "HIGH_CONFIDENCE",
        "confidence": 0.9,
        "reason": "Official developer development and tower list support the OSM name/location; no direct source identifier exists.",
    },
}


def aliases_from_tags(tags: dict[str, str]) -> list[str]:
    values: list[str] = []
    for key in ("name", "name:en", "official_name", "short_name", "alt_name"):
        raw = tags.get(key)
        if raw:
            values.extend(piece.strip() for piece in raw.split(";") if piece.strip())
    return list(dict.fromkeys(values))


def initial_identity(name: str | None, tags: dict[str, str], source_id: str) -> tuple[str, float, str]:
    if tags.get("wikidata") or tags.get("wikipedia"):
        return "CONFIRMED", 0.98, "DIRECT_IDENTIFIER"
    if source_id in OFFICIAL_MATCHES:
        match = OFFICIAL_MATCHES[source_id]
        return match["status"], match["confidence"], "EXACT_OFFICIAL_MATCH"
    address_signals = [tags.get("addr:street"), tags.get("addr:housename"), tags.get("addr:housenumber")]
    if name and any(address_signals):
        return "HIGH_CONFIDENCE", 0.8, "MULTI_SIGNAL_AUTOMATIC"
    if name and not re.fullmatch(r"B:\d+", name):
        return "REVIEW_REQUIRED", 0.55, "OSM_NAME_ONLY"
    if name:
        return "REVIEW_REQUIRED", 0.5, "AMBIGUOUS_SITE_LABEL"
    return "UNRESOLVED", 0.1, "NO_IDENTITY_EVIDENCE"


def next_id(existing_ids: set[str], prefix: str) -> str:
    indexes = [int(match.group(1)) for value in existing_ids if (match := re.fullmatch(fr"{prefix}_(\d+)", value))]
    value = max(indexes, default=0) + 1
    result = f"{prefix}_{value:04d}"
    existing_ids.add(result)
    return result


def serialize_geometry(geometry) -> dict[str, Any]:
    payload = mapping(geometry)
    return json.loads(json.dumps(payload))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=INPUT_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()

    collection = read_json(args.input)
    if not collection or not collection.get("features"):
        raise RuntimeError(f"No building features found in {args.input}")
    old = read_json(args.output, {}) or {}
    old_map = old.get("source_entity_map", {})
    old_entities = old.get("entities", [])
    used_ids = {entity.get("entity_id") for entity in old.get("entities", []) if entity.get("entity_id")}
    assigned_ids: set[str] = set()

    features = collection["features"]
    outlines = [feature for feature in features if feature["properties"]["feature_kind"] == "building_outline"]
    parts = [feature for feature in features if feature["properties"]["feature_kind"] == "building_part"]

    # Merge only the one evidence-backed duplicate-outline pattern: an unnamed outline
    # is almost wholly contained by a named outline and both contain the same part.
    merged_into: dict[str, str] = {}
    for inner in outlines:
        inner_id = inner["properties"]["id"]
        inner_name = inner["properties"].get("name")
        if inner_name:
            continue
        inner_geometry = shape(inner["geometry"])
        contained_parts = {
            part["properties"]["id"]
            for part in parts
            if inner_geometry.covers(shape(part["geometry"]).representative_point())
        }
        for outer in outlines:
            if not outer["properties"].get("name"):
                continue
            outer_geometry = shape(outer["geometry"])
            ratio = inner_geometry.intersection(outer_geometry).area / max(inner_geometry.area, 1e-9)
            shared_part = any(outer_geometry.covers(shape(part["geometry"]).representative_point()) for part in parts if part["properties"]["id"] in contained_parts)
            if ratio >= 0.98 and shared_part:
                merged_into[inner_id] = outer["properties"]["id"]
                break

    canonical_groups: dict[str, list[dict[str, Any]]] = {}
    for feature in outlines:
        source_id = feature["properties"]["id"]
        root_source = merged_into.get(source_id, source_id)
        canonical_groups.setdefault(root_source, []).append(feature)

    source_entity_map = dict(old_map)
    entities: list[dict[str, Any]] = []
    entity_by_source: dict[str, dict[str, Any]] = {}
    inverse = Transformer.from_crs(collection["projected_crs"], collection["source_crs"], always_xy=True)
    origin = collection["local_frame"]["origin_projected"]

    for root_source in sorted(canonical_groups):
        group = canonical_groups[root_source]
        source_ids = sorted(feature["properties"]["id"] for feature in group)
        named = [feature for feature in group if feature["properties"].get("name")]
        primary = named[0] if named else group[0]
        props = primary["properties"]
        tags = props.get("tags", {})
        name = props.get("name")
        official = OFFICIAL_MATCHES.get(root_source)
        if official:
            name = official["canonical_name"]
        status, confidence, method = initial_identity(name, tags, root_source)
        geometries = [shape(feature["geometry"]) for feature in group]
        geometry = unary_union(geometries)
        center = geometry.centroid
        entity_id = next((source_entity_map.get(source) for source in source_ids if source_entity_map.get(source)), None)
        id_reuse_method = "PERSISTED_SOURCE_MAPPING" if entity_id else None
        if not entity_id and name:
            candidates = [
                old_entity for old_entity in old_entities
                if old_entity.get("entity_id") not in assigned_ids
                and old_entity.get("normalized_name") == normalize_name(name)
                and abs(old_entity.get("centroid", {}).get("local_x_m", 1e9) - center.x) <= 15
                and abs(old_entity.get("centroid", {}).get("local_y_m", 1e9) - center.y) <= 15
            ]
            if len(candidates) == 1:
                entity_id = candidates[0]["entity_id"]
                id_reuse_method = "EXACT_NAME_AND_SPATIAL_CONTINUITY"
        if not entity_id:
            entity_id = next_id(used_ids, "bgc_building")
            id_reuse_method = "NEW_APPEND_ONLY_ID"
        assigned_ids.add(entity_id)
        for source in source_ids:
            source_entity_map[source] = entity_id
        lon, lat = inverse.transform(center.x + origin["easting"], center.y + origin["northing"])
        aliases = list(dict.fromkeys(alias for feature in group for alias in aliases_from_tags(feature["properties"].get("tags", {}))))
        if props.get("name") and props.get("name") not in aliases:
            aliases.append(props["name"])
        entity = {
            "entity_id": entity_id,
            "entity_type": "BUILDING_STRUCTURE" if tags.get("building") == "roof" else "BUILDING",
            "canonical_name": name,
            "normalized_name": normalize_name(name),
            "aliases": aliases,
            "status": "ACTIVE",
            "identity_status": status,
            "identity_confidence": confidence,
            "decision_method": method,
            "id_assignment_method": id_reuse_method,
            "decision_timestamp": "2026-09-11",
            "supporting_evidence": ([official["reason"]] if official else ["OSM tags and footprint location"]),
            "centroid": {"longitude": round(lon, 7), "latitude": round(lat, 7), "local_x_m": round(center.x, 3), "local_y_m": round(center.y, 3)},
            "footprint_reference": "data/processed/pilot-buildings.geojson",
            "geographic_feature_ids": source_ids,
            "osm_ids": source_ids,
            "building_part_ids": [],
            "wikidata_id": tags.get("wikidata"),
            "wikipedia_url": tags.get("wikipedia"),
            "official_url": official.get("official_url") if official else tags.get("website"),
            "official_address": None,
            "parent_entity_id": None,
            "child_entity_ids": [],
            "source_ids": ["source:osm", *(official.get("source_ids", []) if official else [])],
            "height": {
                "value_m": props.get("height_m"),
                "status": props.get("height_status"),
                "method": props.get("height_method"),
                "confidence": props.get("height_confidence"),
                "source_ids": ["source:osm"] if props.get("height_status") == "VERIFIED_GEOGRAPHIC" else [],
                "levels": props.get("levels"),
            },
            "tags": tags,
        }
        entities.append(entity)
        for source_id in source_ids:
            entity_by_source[source_id] = entity

    part_relationships: list[dict[str, Any]] = []
    review_items: list[dict[str, Any]] = []
    for part in parts:
        part_id = part["properties"]["id"]
        part_geometry = shape(part["geometry"])
        candidates: list[tuple[float, dict[str, Any]]] = []
        for outline in outlines:
            outline_geometry = shape(outline["geometry"])
            ratio = part_geometry.intersection(outline_geometry).area / max(part_geometry.area, 1e-9)
            if ratio >= 0.98:
                candidates.append((ratio, outline))
        target_ids = list(dict.fromkeys(source_entity_map[candidate["properties"]["id"]] for _, candidate in candidates))
        if len(target_ids) == 1:
            target = next(entity for entity in entities if entity["entity_id"] == target_ids[0])
            target["building_part_ids"].append(part_id)
            target["height"].setdefault("components", []).append({
                "source_feature_id": part_id,
                "value_m": part["properties"].get("height_m"),
                "status": part["properties"].get("height_status"),
                "method": part["properties"].get("height_method"),
            })
            if (
                part["properties"].get("height_status") == "VERIFIED_GEOGRAPHIC"
                and (target["height"].get("status") != "VERIFIED_GEOGRAPHIC" or part["properties"].get("height_m", 0) > target["height"].get("value_m", 0))
            ):
                target["height"].update({
                    "value_m": part["properties"].get("height_m"),
                    "status": "VERIFIED_GEOGRAPHIC",
                    "method": "maximum_explicit_osm_building_part_height",
                    "confidence": part["properties"].get("height_confidence"),
                    "source_ids": ["source:osm"],
                    "levels": part["properties"].get("levels"),
                })
            source_entity_map[part_id] = target["entity_id"]
            part_relationships.append({
                "part_id": part_id,
                "parent_entity_id": target["entity_id"],
                "status": "HIGH_CONFIDENCE",
                "method": "GEOMETRIC_CONTAINMENT",
                "coverage_ratio": round(max(value for value, _ in candidates), 4),
                "supporting_outline_ids": sorted(candidate["properties"]["id"] for _, candidate in candidates),
            })
        else:
            entity_id = source_entity_map.get(part_id) or next_id(used_ids, "bgc_building")
            source_entity_map[part_id] = entity_id
            center = part_geometry.centroid
            lon, lat = inverse.transform(center.x + origin["easting"], center.y + origin["northing"])
            entity = {
                "entity_id": entity_id,
                "entity_type": "BUILDING_FRAGMENT",
                "canonical_name": None,
                "normalized_name": None,
                "aliases": [],
                "status": "ACTIVE",
                "identity_status": "UNRESOLVED",
                "identity_confidence": 0.1,
                "decision_method": "NO_PARENT_CONTAINMENT",
                "decision_timestamp": "2026-09-11",
                "supporting_evidence": ["Part intersects no in-pilot building outline; its parent may lie outside the clipped pilot."],
                "centroid": {"longitude": round(lon, 7), "latitude": round(lat, 7), "local_x_m": round(center.x, 3), "local_y_m": round(center.y, 3)},
                "footprint_reference": "data/processed/pilot-buildings.geojson",
                "geographic_feature_ids": [part_id],
                "osm_ids": [part_id],
                "building_part_ids": [part_id],
                "wikidata_id": None,
                "wikipedia_url": None,
                "official_url": None,
                "official_address": None,
                "parent_entity_id": None,
                "child_entity_ids": [],
                "source_ids": ["source:osm"],
                "height": {
                    "value_m": part["properties"].get("height_m"),
                    "status": part["properties"].get("height_status"),
                    "method": part["properties"].get("height_method"),
                    "confidence": part["properties"].get("height_confidence"),
                    "source_ids": ["source:osm"],
                    "levels": part["properties"].get("levels"),
                },
                "tags": part["properties"].get("tags", {}),
            }
            entities.append(entity)
            review_items.append({
                "review_id": f"review:entity:{part_id.replace(':', '-')}",
                "candidate": part_id,
                "possible_entity_id": None,
                "evidence": ["No containing outline in pilot", "Feature is tagged building:part"],
                "recommended_action": "REVIEW_PARENT_OUTSIDE_PILOT",
            })
            part_relationships.append({"part_id": part_id, "parent_entity_id": None, "status": "UNRESOLVED", "method": "NO_PARENT_CONTAINMENT"})

    # Explicit complex membership is separate from building-part containment.
    complexes: list[dict[str, Any]] = []
    complex_specs = [
        ("bgc_complex_0001", "Bonifacio High Street", "CONFIRMED", "source:official-ayala-bonifacio-high-street", lambda e: "bonifacio high street" in " ".join(filter(None, [e.get("canonical_name"), e.get("tags", {}).get("addr:housename")])).lower() or (e.get("canonical_name") in {"C1", "C2", "C3", "Live Street", "Central Square"})),
        ("bgc_complex_0002", "High Street South", "HIGH_CONFIDENCE", "source:official-alveo-high-street-south", lambda e: bool(e.get("canonical_name")) and any(token in e["canonical_name"].lower() for token in ("maridien", "verve", "west gallery", "high street south"))),
    ]
    for complex_id, name, identity_status, source_id, predicate in complex_specs:
        members = sorted(entity["entity_id"] for entity in entities if predicate(entity))
        if not members:
            continue
        complexes.append({
            "entity_id": complex_id,
            "entity_type": "BUILDING_COMPLEX",
            "canonical_name": name,
            "normalized_name": normalize_name(name),
            "aliases": [],
            "status": "ACTIVE",
            "identity_status": identity_status,
            "identity_confidence": 0.95 if identity_status == "CONFIRMED" else 0.85,
            "decision_method": "EXACT_OFFICIAL_MATCH",
            "decision_timestamp": "2026-09-11",
            "supporting_evidence": ["Official developer/operator source names the development; membership uses explicit OSM names and address tags."],
            "child_entity_ids": members,
            "source_ids": [source_id],
        })
        for entity in entities:
            if entity["entity_id"] in members and entity["parent_entity_id"] is None:
                entity["parent_entity_id"] = complex_id

    # Nested named buildings create reviewable relationships, not automatic merges.
    for child_source, parent_source in (("osm:way:603380324", "osm:way:27442969"),):
        child = entity_by_source.get(child_source)
        parent = entity_by_source.get(parent_source)
        if child and parent:
            child["parent_entity_id"] = parent["entity_id"]
            parent["child_entity_ids"].append(child["entity_id"])
            review_items.append({
                "review_id": "review:entity:bench-b5",
                "candidate": child_source,
                "possible_entity_id": parent["entity_id"],
                "evidence": ["Footprint is fully contained by B:5", "addr:housename says B:5, Bonifacio High Street", "Name/brand identifies a tenant"],
                "recommended_action": "KEEP_CHILD_ENTITY_REVIEW_BUILDING_VS_TENANT",
            })

    duplicate_names: dict[str, list[str]] = {}
    for entity in entities:
        if entity.get("normalized_name"):
            duplicate_names.setdefault(entity["normalized_name"], []).append(entity["entity_id"])
    for normalized, ids in duplicate_names.items():
        if len(ids) > 1:
            for entity in entities:
                if entity["entity_id"] in ids:
                    entity["identity_status"] = "REVIEW_REQUIRED"
                    entity["identity_confidence"] = min(entity["identity_confidence"], 0.55)
                    entity["decision_method"] = "AMBIGUOUS_DUPLICATE_NAME"
                    entity["supporting_evidence"].append("Name is shared by multiple distinct pilot footprints.")
            review_items.append({
                "review_id": f"review:entity:duplicate-{normalized.replace(' ', '-')}",
                "candidate": normalized,
                "possible_entity_ids": sorted(ids),
                "evidence": ["Canonical/OSM name is shared by multiple distinct footprints"],
                "recommended_action": "REVIEW_ALIAS_DISAMBIGUATION",
            })

    for entity in entities:
        if entity["identity_status"] in {"REVIEW_REQUIRED", "UNRESOLVED"}:
            review_items.append({
                "review_id": f"review:identity:{entity['entity_id']}",
                "candidate": entity.get("canonical_name") or entity["geographic_feature_ids"],
                "possible_entity_id": entity["entity_id"],
                "evidence": entity["supporting_evidence"],
                "recommended_action": "REVIEW" if entity["identity_status"] == "REVIEW_REQUIRED" else "RESEARCH_IDENTITY",
            })

    entities.sort(key=lambda entity: entity["entity_id"])
    complexes.sort(key=lambda entity: entity["entity_id"])
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "schema_version": 1,
        "dataset_id": "pilot-canonical-entities-v1",
        "generated_at": now,
        "source_dataset": str(args.input.relative_to(ROOT)).replace("\\", "/"),
        "source_sha256": collection.get("source_sha256"),
        "id_policy": "Persistent project-owned IDs; existing source mappings are reused and new IDs are append-only.",
        "counts": {
            "raw_geographic_records": len(features),
            "building_outlines": len(outlines),
            "building_parts": len(parts),
            "canonical_building_entities": len(entities),
            "building_complexes": len(complexes),
            "building_parts_resolved": sum(item["status"] != "UNRESOLVED" for item in part_relationships),
            "building_parts_unresolved": sum(item["status"] == "UNRESOLVED" for item in part_relationships),
        },
        "source_entity_map": source_entity_map,
        "part_relationships": part_relationships,
        "entities": entities,
        "complexes": complexes,
        "content_sha256": stable_hash({"entities": entities, "complexes": complexes}),
    }
    write_json(args.output, payload)
    write_json(ALIASES_PATH, {
        "schema_version": 1,
        "generated_at": now,
        "aliases": [
            {"entity_id": entity["entity_id"], "alias": alias, "normalized_alias": normalize_name(alias), "source_id": "source:osm"}
            for entity in entities
            for alias in entity.get("aliases", [])
        ],
    })
    write_json(REVIEW_PATH, {"schema_version": 1, "generated_at": now, "items": review_items})
    print(
        "BGC_ENTITIES: "
        f"raw={len(features)} buildings={len(entities)} complexes={len(complexes)} "
        f"parts_resolved={payload['counts']['building_parts_resolved']}/{len(parts)} reviews={len(review_items)}"
    )


if __name__ == "__main__":
    main()
