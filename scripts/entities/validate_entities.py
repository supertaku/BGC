"""Validate M5 entity IDs, source mappings, part links, and confidence enums."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from evidence.model import read_json  # noqa: E402


def main() -> None:
    payload = read_json(ROOT / "data" / "entities" / "pilot-entities.json")
    entities = payload["entities"]
    ids = [entity["entity_id"] for entity in entities]
    assert len(ids) == len(set(ids)), "Duplicate project entity IDs"
    assert all(value.startswith("bgc_building_") for value in ids), "Unexpected building ID namespace"
    assert len(payload["source_entity_map"]) >= payload["counts"]["raw_geographic_records"], "Every raw building/part must map to one canonical entity"
    valid_statuses = {"CONFIRMED", "HIGH_CONFIDENCE", "REVIEW_REQUIRED", "UNRESOLVED", "REJECTED"}
    assert all(entity["identity_status"] in valid_statuses for entity in entities), "Invalid identity status"
    relationships = payload["part_relationships"]
    assert len(relationships) == payload["counts"]["building_parts"], "Missing building-part relationship"
    assert sum(item["status"] != "UNRESOLVED" for item in relationships) == 7, "Pilot part grouping regression"
    print(f"BGC_ENTITY_VALIDATE: PASS entities={len(entities)} mappings={len(payload['source_entity_map'])} parts=7/8")


if __name__ == "__main__":
    main()
