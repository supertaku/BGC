from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from blender.framework.geometry import FacadeFrame, OpenFacadeBand, WindowGrid
from scripts.reconstruction.spec_contract import SCHEMA_VERSION, validate_spec
from scripts.reconstruction.update_asset_registry import validate_asset_path


class M8ToolingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = ROOT / "data/reconstruction_packages/synthetic_framework_fixture"
        cls.base_spec = json.loads((cls.fixture / "reconstruction_spec.json").read_text(encoding="utf-8"))

    def validate_mutation(self, mutate) -> str:
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "synthetic_framework_fixture"
            shutil.copytree(self.fixture, package)
            mutate(package)
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/reconstruction/validate_package.py"), str(package), "--json"],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0, result.stdout)
            return result.stdout

    def mutate_json(self, package: Path, name: str, mutation) -> None:
        path = package / name
        payload = json.loads(path.read_text(encoding="utf-8"))
        mutation(payload)
        path.write_text(json.dumps(payload), encoding="utf-8")

    def test_contract_and_version(self):
        model = validate_spec(self.base_spec)
        self.assertEqual(model["schema_version"], SCHEMA_VERSION)

    def test_facade_frame_uses_normalized_coordinates(self):
        region = FacadeFrame((0, 0), 40, 20, 0).region(0.25, 0.75, 0.1, 0.6)
        self.assertEqual(region["width_m"], 20)
        self.assertEqual(region["height_m"], 10)

    def test_window_grid_is_deterministic_and_normalized(self):
        regions = WindowGrid(3, 2, 0.1, 0.9, 0.2, 0.8).regions()
        self.assertEqual(len(regions), 6)
        self.assertTrue(all(0 <= value <= 1 for region in regions for value in region))
        self.assertEqual(regions, WindowGrid(3, 2, 0.1, 0.9, 0.2, 0.8).regions())

    def test_open_facade_band_preserves_open_zone(self):
        parts = OpenFacadeBand(5.0, 4.2).parts()
        self.assertGreater(parts["open_zone"][1], 0)
        self.assertAlmostEqual(parts["top_slab"][0] + parts["top_slab"][1], 9.2)

    def test_missing_entity_id(self):
        output = self.validate_mutation(lambda p: self.mutate_json(p, "reconstruction_spec.json", lambda x: x["target"].pop("entity_id")))
        self.assertIn("target.entity_id", output)

    def test_invalid_material_reference(self):
        output = self.validate_mutation(lambda p: self.mutate_json(p, "facades.json", lambda x: x["facades"][0]["material_regions"].append("mat:missing")))
        self.assertIn("unresolved facade material IDs", output)

    def test_unknown_observation_id(self):
        output = self.validate_mutation(lambda p: self.mutate_json(p, "reconstruction_spec.json", lambda x: x["generic_builder"]["volumes"][0]["observation_ids"].append("obs:missing")))
        self.assertIn("unknown observation IDs", output)

    def test_malformed_facade_segment(self):
        output = self.validate_mutation(lambda p: self.mutate_json(p, "reconstruction_spec.json", lambda x: x["generic_builder"]["facade_regions"][0].update({"u0": 0.9, "u1": 0.2})))
        self.assertIn("malformed normalized segment", output)

    def test_unsupported_schema_version(self):
        output = self.validate_mutation(lambda p: self.mutate_json(p, "reconstruction_spec.json", lambda x: x.update({"schema_version": "9.0"})))
        self.assertIn("unsupported reconstruction schema version", output)

    def test_duplicate_component_id(self):
        output = self.validate_mutation(lambda p: self.mutate_json(p, "reconstruction_spec.json", lambda x: x["generic_builder"]["volumes"][1].update({"component_id": x["generic_builder"]["volumes"][0]["component_id"]})))
        self.assertIn("duplicate component IDs", output)

    def test_missing_geometry_file(self):
        output = self.validate_mutation(lambda p: self.mutate_json(p, "reconstruction_spec.json", lambda x: x.update({"geometry_file": "missing.geojson"})))
        self.assertIn("geometry_file references missing file", output)

    def test_invalid_glb_path(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "asset path"):
                validate_asset_path(Path(directory), {"asset": "missing.glb"}, {"file_size_bytes": 1})


if __name__ == "__main__":
    unittest.main()
