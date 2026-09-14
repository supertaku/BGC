from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

from shapely.geometry import Polygon


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "geography"))

from fetch_osm import build_query
from normalize_osm import height_observation, min_height_observation


class M11WholeBgcTests(unittest.TestCase):
    def test_whole_boundary_query_has_required_layers_without_pois(self):
        query = build_query((14.53, 121.04, 14.57, 121.07), "whole-city")
        self.assertIn('["building"]', query)
        self.assertIn('["building:part"]', query)
        self.assertIn('way["highway"]', query)
        self.assertIn('["leisure"', query)
        self.assertNotIn('["amenity"]', query)
        self.assertNotIn('["barrier"]', query)

    def test_height_precedence_and_min_level(self):
        self.assertEqual(height_observation({"height": "41 m", "building:levels": "50"})["height_m"], 41)
        self.assertEqual(height_observation({"building:levels": "10"})["status"], "ESTIMATED")
        self.assertEqual(height_observation({"building": "yes"})["status"], "PROCEDURAL")
        self.assertEqual(min_height_observation({"building:min_level": "2"})["min_height_m"], 6.4)

    def test_centroid_ownership_is_stable_at_boundaries(self):
        footprint = Polygon([(0, 0), (300, 0), (300, 100), (0, 100)])
        origin_x = -250
        column = int((footprint.centroid.x - origin_x) // 250)
        self.assertEqual(column, 1)

    def test_manifest_is_complete_and_duplicate_free_when_generated(self):
        path = ROOT / "exports" / "bgc" / "manifest.json"
        if not path.is_file():
            self.skipTest("M11 manifest has not been generated")
        manifest = json.loads(path.read_text(encoding="utf-8"))
        tile_ids = [tile["tile_id"] for tile in manifest["tiles"]]
        self.assertEqual(len(tile_ids), len(set(tile_ids)))
        entities = [entity for tile in manifest["tiles"] for entity in tile["entities"]]
        self.assertEqual(len(entities), len(set(entities)))
        self.assertTrue(all(tile["status"] == "PASS" for tile in manifest["tiles"]))
        self.assertEqual(manifest["totals"]["canonical_buildings"], len(entities))

    def test_existing_seven_lod1_assets_remain_registered(self):
        registry = json.loads((ROOT / "data" / "assets" / "buildings.json").read_text(encoding="utf-8"))
        approved = [entry for entry in registry["buildings"].values() if entry.get("available_lods", {}).get("1", {}).get("status") == "APPROVED"]
        self.assertEqual(len(approved), 7)


if __name__ == "__main__":
    unittest.main()
