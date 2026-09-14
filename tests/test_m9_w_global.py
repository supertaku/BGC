from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data" / "reconstruction_packages" / "bgc_building_0007"


def load(name: str):
    return json.loads((PACKAGE / name).read_text(encoding="utf-8"))


class M9WGlobalTests(unittest.TestCase):
    def test_package_contract_validates(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/reconstruction/validate_package.py"), str(PACKAGE), "--json"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "VALID_WITH_GAPS")

    def test_cold_read_contract_is_self_contained(self):
        entity, spec, coverage, unknowns = load("entity.json"), load("reconstruction_spec.json"), load("coverage.json"), load("unknowns.json")
        self.assertEqual(entity["canonical_name"], "W Global Center")
        self.assertIn("9th Avenue corner 30th Street", spec["target"]["location"])
        self.assertEqual(spec["known_dimensions"]["maximum_height_m"], 30.5)
        self.assertEqual(coverage["reconstruction_readiness"], "RECONSTRUCTION_READY_WITH_GAPS")
        self.assertGreaterEqual(len(unknowns["unknowns"]), 6)
        self.assertTrue(spec["do_not_invent"])

    def test_floor_conflict_is_preserved(self):
        conflict = next(item for item in load("observations.json")["observations"] if item["observation_id"] == "obs:wgc:floor-conflict")
        self.assertEqual(conflict["status"], "CONFLICTED")
        self.assertEqual({claim["value"] for claim in conflict["value"]["claims"]}, {7, 8})
        self.assertIn("Unresolved", conflict["value"]["final_modeling_interpretation"])

    def test_research_only_media_is_not_redistributable(self):
        rights = load("rights.json")["references"]
        self.assertTrue(rights)
        self.assertTrue(all(item["rights_status"] == "RESEARCH_ONLY" for item in rights))
        self.assertTrue(all(not item["local_copy_allowed"] and not item["derivative_use_allowed"] and not item["redistribution_allowed"] for item in rights))

    def test_registry_preserves_lod2_and_adds_lod1(self):
        registry = json.loads((ROOT / "data/assets/buildings.json").read_text(encoding="utf-8"))
        lods = registry["buildings"]["bgc_building_0007"]["available_lods"]
        self.assertEqual(lods["1"]["status"], "APPROVED")
        self.assertEqual(lods["2"]["status"], "AVAILABLE")


if __name__ == "__main__":
    unittest.main()
