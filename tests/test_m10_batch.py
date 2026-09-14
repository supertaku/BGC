from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]


class M10BatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.batch = json.loads((ROOT / "data/batches/m10-batch.json").read_text(encoding="utf-8"))

    def test_two_wave_diverse_batch(self):
        targets = self.batch["targets"]
        self.assertEqual(len(targets), 5)
        self.assertEqual(sum(item["wave"] == "A" for item in targets), 2)
        self.assertEqual(sum(item["wave"] == "B" for item in targets), 3)
        self.assertGreaterEqual(len({item["archetype"] for item in targets}), 4)

    def test_candidate_pool_is_complete_and_transparent(self):
        report = json.loads((ROOT / "data/reports/m10-candidate-pool.json").read_text(encoding="utf-8"))
        self.assertEqual(report["candidate_count"], 29)
        self.assertEqual(sum(item["selected"] for item in report["candidates"]), 5)
        self.assertTrue(all(len(item["selection_dimensions"]) == 7 for item in report["candidates"]))

    def test_all_packages_validate(self):
        for target in self.batch["targets"]:
            package = ROOT / "data/reconstruction_packages" / target["entity_id"]
            result = subprocess.run([sys.executable, str(ROOT / "scripts/reconstruction/validate_package.py"), str(package), "--json"], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout)["status"], "VALID_WITH_GAPS")

    def test_non_rectilinear_target_uses_real_polygon(self):
        package = ROOT / "data/reconstruction_packages/bgc_building_0011"
        geometry = json.loads((package / "geometry.geojson").read_text(encoding="utf-8"))
        ring = geometry["features"][0]["geometry"]["coordinates"][0]
        self.assertGreater(len(ring) - 1, 4)
        spec = json.loads((package / "reconstruction_spec.json").read_text(encoding="utf-8"))
        self.assertTrue(spec["generic_builder"]["polygon_edge_regions"])

    def test_assets_keep_lod2_and_validated_lod1(self):
        registry = json.loads((ROOT / "data/assets/buildings.json").read_text(encoding="utf-8"))
        for target in self.batch["targets"]:
            entry = registry["buildings"][target["entity_id"]]
            self.assertEqual(entry["available_lods"]["1"]["status"], "APPROVED")
            self.assertEqual(entry["available_lods"]["2"]["status"], "AVAILABLE")
            metrics = json.loads((ROOT / entry["available_lods"]["1"]["metrics"]).read_text(encoding="utf-8"))
            self.assertEqual(metrics["validation"], "PASS")


if __name__ == "__main__":
    unittest.main()
