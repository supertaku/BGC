from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from evidence.model import dedupe_reference_records, resolve_observations, review_rights  # noqa: E402
from entities.resolve_entities import initial_identity  # noqa: E402


class EntityResolutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entities = json.loads((ROOT / "data/entities/pilot-entities.json").read_text(encoding="utf-8"))
        cls.reviews = json.loads((ROOT / "data/review/entity-match-review.json").read_text(encoding="utf-8"))

    def test_direct_identifier_resolves_confirmed(self):
        status, _, method = initial_identity("Example", {"wikidata": "Q1"}, "osm:way:1")
        self.assertEqual((status, method), ("CONFIRMED", "DIRECT_IDENTIFIER"))

    def test_alias_does_not_create_false_duplicate(self):
        b3 = [entity for entity in self.entities["entities"] if entity.get("canonical_name") == "B:3"]
        self.assertEqual(len(b3), 2)
        self.assertEqual(len({entity["entity_id"] for entity in b3}), 2)

    def test_building_parts_map_to_expected_parent(self):
        relationships = self.entities["part_relationships"]
        self.assertEqual(sum(item["status"] != "UNRESOLVED" for item in relationships), 7)
        self.assertEqual(sum(item["status"] == "UNRESOLVED" for item in relationships), 1)

    def test_ambiguous_name_enters_review_queue(self):
        self.assertTrue(any(item["review_id"] == "review:entity:duplicate-b-3" for item in self.reviews["items"]))


class ReferenceTests(unittest.TestCase):
    def test_same_source_id_is_duplicate(self):
        records, count = dedupe_reference_records([
            {"source_id": "commons", "source_item_id": "1", "entity_links": [{"entity_id": "a"}]},
            {"source_id": "commons", "source_item_id": "1", "entity_links": [{"entity_id": "b"}]},
        ])
        self.assertEqual((len(records), count), (1, 1))
        self.assertEqual(len(records[0]["entity_links"]), 2)

    def test_same_sha1_is_duplicate(self):
        records, count = dedupe_reference_records([{"source_hash": "abc"}, {"source_hash": "abc"}])
        self.assertEqual((len(records), count), (1, 1))

    def test_different_references_survive(self):
        records, _ = dedupe_reference_records([{"source_item_id": "1"}, {"source_item_id": "2"}])
        self.assertEqual(len(records), 2)

    def test_missing_license_requires_review(self):
        self.assertEqual(review_rights(None, None, None)["rights_status"], "REVIEW_REQUIRED")

    def test_sharealike_and_attribution_survive(self):
        rights = review_rights("CC BY-SA 4.0", "https://creativecommons.org/licenses/by-sa/4.0", "Creator")
        self.assertTrue(rights["attribution_required"])
        self.assertTrue(rights["share_alike_required"])

    def test_pilot_reference_links_and_sources_are_valid(self):
        entities = json.loads((ROOT / "data/entities/pilot-entities.json").read_text(encoding="utf-8"))
        references = json.loads((ROOT / "data/references/references.json").read_text(encoding="utf-8"))
        sources = json.loads((ROOT / "data/sources/sources.json").read_text(encoding="utf-8"))
        entity_ids = {item["entity_id"] for item in entities["entities"]}
        source_ids = {item["source_id"] for item in sources["sources"]}
        for reference in references["records"]:
            self.assertIn(reference["source_id"], source_ids)
            self.assertTrue(all(link["entity_id"] in entity_ids for link in reference["entity_links"]))
            self.assertIsNone(reference.get("local_file_path"))


class ObservationAndCoverageTests(unittest.TestCase):
    def test_weak_does_not_override_strong(self):
        result = resolve_observations([
            {"value": 20, "status": "ESTIMATED", "confidence": 0.9},
            {"value": 18, "status": "VERIFIED_AUTHORITATIVE", "confidence": 0.8},
        ])
        self.assertEqual(result["selected"]["value"], 18)

    def test_equal_strength_conflict_is_retained(self):
        result = resolve_observations([
            {"value": 20, "status": "VERIFIED_GEOGRAPHIC", "confidence": 0.8},
            {"value": 21, "status": "VERIFIED_GEOGRAPHIC", "confidence": 0.7},
        ])
        self.assertTrue(result["conflicted"])
        self.assertEqual(len(result["candidates"]), 2)

    def test_inferred_viewpoint_not_verified_facade(self):
        coverage = json.loads((ROOT / "data/references/coverage.json").read_text(encoding="utf-8"))
        self.assertTrue(all(item["facade_depicted"] == "UNKNOWN" for item in coverage["entities"]))


if __name__ == "__main__":
    unittest.main()
