"""Compute visible per-entity coverage dimensions and reconstruction readiness."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from evidence.model import read_json, write_json  # noqa: E402

ENTITIES_PATH = ROOT / "data" / "entities" / "pilot-entities.json"
REFERENCES_PATH = ROOT / "data" / "references" / "references.json"
OUTPUT_PATH = ROOT / "data" / "references" / "coverage.json"


def main() -> None:
    entities = read_json(ENTITIES_PATH)["entities"]
    references = read_json(REFERENCES_PATH, {}).get("records", [])
    result = []
    for entity in entities:
        entity_id = entity["entity_id"]
        linked = [record for record in references if any(link["entity_id"] == entity_id for link in record.get("entity_links", []))]
        visual = [record for record in linked if record.get("asset_url") or record.get("thumbnail_url")]
        accepted_visual = [record for record in visual if record.get("entity_match_status") == "ACCEPTED"]
        reusable = [record for record in accepted_visual if record.get("rights_status") == "REUSE_CAPABLE"]
        research_only = [record for record in linked if record.get("rights_status") == "RESEARCH_ONLY"]
        pending = [record for record in visual if record.get("entity_match_status") == "REVIEW_REQUIRED"]
        if len(accepted_visual) >= 2:
            imagery = "GOOD"
        elif len(accepted_visual) == 1:
            imagery = "PARTIAL"
        elif pending:
            imagery = "WEAK"
        else:
            imagery = "NONE"
        height_status = entity["height"]["status"]
        massing = "GOOD" if height_status.startswith("VERIFIED") else "PARTIAL" if height_status == "ESTIMATED" else "WEAK"
        identity_good = entity["identity_status"] in {"CONFIRMED", "HIGH_CONFIDENCE"}
        readiness = "MEDIUM" if identity_good and height_status != "PROCEDURAL" and imagery in {"GOOD", "PARTIAL"} else "LOW" if identity_good else "NOT_READY"
        recommended_tier = "TIER_B_CANDIDATE" if readiness == "MEDIUM" else "TIER_C"
        result.append({
            "entity_id": entity_id,
            "canonical_name": entity.get("canonical_name"),
            "identity": entity["identity_status"],
            "height_evidence": height_status,
            "massing_evidence": massing,
            "overall_imagery": imagery,
            "identity_reference_ids": [record["reference_id"] for record in linked if record.get("reference_role") == "IDENTITY"],
            "accepted_visual_reference_ids": [record["reference_id"] for record in accepted_visual],
            "pending_visual_reference_ids": [record["reference_id"] for record in pending],
            "reusable_reference_ids": [record["reference_id"] for record in reusable],
            "research_only_reference_ids": [record["reference_id"] for record in research_only],
            "aspects": {
                "north_side_evidence": {"rating": "NONE", "reference_ids": []},
                "south_side_evidence": {"rating": "NONE", "reference_ids": []},
                "east_side_evidence": {"rating": "NONE", "reference_ids": []},
                "west_side_evidence": {"rating": "NONE", "reference_ids": []},
                "entrance": {"rating": "NONE", "reference_ids": []},
                "podium": {"rating": "NONE", "reference_ids": []},
                "roof": {"rating": "NONE", "reference_ids": []},
                "aerial_context": {"rating": "NONE", "reference_ids": []},
                "materials": {"rating": "NONE", "reference_ids": []},
                "street_context": {"rating": imagery, "reference_ids": [record["reference_id"] for record in accepted_visual]},
            },
            "viewpoint_side_status": "UNKNOWN",
            "facade_depicted": "UNKNOWN",
            "important_missing_evidence": ["directionally verified facade views", "entrance view", "roof/aerial view"],
            "recommended_fidelity_tier": recommended_tier,
            "reconstruction_readiness": readiness,
        })
    write_json(OUTPUT_PATH, {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(), "rating_policy": "Counts are decision coverage, not image volume. Camera side and depicted facade remain separate.", "entities": result})
    counts = {rating: sum(item["overall_imagery"] == rating for item in result) for rating in ("GOOD", "PARTIAL", "WEAK", "NONE")}
    print("BGC_COVERAGE: " + " ".join(f"{key.lower()}={value}" for key, value in counts.items()))


if __name__ == "__main__":
    main()

