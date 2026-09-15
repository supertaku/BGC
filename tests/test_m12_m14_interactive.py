import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "web" / "public" / "world" / "bgc-interactive.json"
TILES = ROOT / "web" / "public" / "world" / "tiles"
WORLD = ROOT / "web" / "public" / "world" / "bgc-world.json"
GENERATOR = ROOT / "scripts" / "geography" / "build_interactive_runtime.py"


class InteractiveRuntimeTests(unittest.TestCase):
    def test_all_world_tiles_have_matching_sidecars(self):
        world = json.loads(WORLD.read_text(encoding="utf-8"))
        expected = {tile["tile_id"] for tile in world["tiles"]}
        actual = {path.stem for path in TILES.glob("tile_*.json")}
        self.assertEqual(expected, actual)
        self.assertEqual(len(actual), 94)

    def test_footprint_ownership_is_unique(self):
        owners = {}
        for path in sorted(TILES.glob("tile_*.json")):
            tile = json.loads(path.read_text(encoding="utf-8"))
            for footprint in tile["footprints"]:
                entity_id = footprint["entity_id"]
                self.assertNotIn(entity_id, owners, f"duplicate owner for {entity_id}")
                owners[entity_id] = tile["tile_id"]
                self.assertTrue(footprint["rings"])
        self.assertEqual(len(owners), 6966)

    def test_environment_is_grounded_and_counted(self):
        index = json.loads(INDEX.read_text(encoding="utf-8"))
        observed = {}
        for path in sorted(TILES.glob("tile_*.json")):
            tile = json.loads(path.read_text(encoding="utf-8"))
            for asset_type, instances in tile["environment"].items():
                observed[asset_type] = observed.get(asset_type, 0) + len(instances)
                self.assertTrue(all(item["grounding"] == "VERIFIED_GEOGRAPHIC" for item in instances))
        self.assertEqual(index["environment_counts"], observed)
        self.assertEqual(index["procedural_environment_count"], 0)
        self.assertEqual(sum(observed.values()), 452)

    def test_lod_and_search_index_contract(self):
        index = json.loads(INDEX.read_text(encoding="utf-8"))
        self.assertEqual(len(index["lod1_entity_ids"]), 7)
        indexed_lods = {entity["detailed_asset_id"] for entity in index["entities"] if entity["detailed_asset_id"]}
        self.assertEqual(set(index["lod1_entity_ids"]), indexed_lods)
        self.assertTrue(all(entity["name"] or entity["detailed_asset_id"] for entity in index["entities"]))

    def test_generator_is_byte_deterministic(self):
        before = hashlib.sha256(INDEX.read_bytes()).hexdigest()
        subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, check=True, capture_output=True, text=True)
        after = hashlib.sha256(INDEX.read_bytes()).hexdigest()
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
