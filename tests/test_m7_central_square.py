from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CentralSquareM7Tests(unittest.TestCase):
    def test_summary_records_validated_lod1(self):
        summary = json.loads((ROOT / "data/reports/m7-summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["phase"], "PASS")
        self.assertEqual(summary["standalone_asset"]["validation"], "PASS")
        self.assertEqual(summary["standalone_asset"]["triangles"], 356)
        self.assertFalse(summary["astra_required_next"])

    def test_qa_has_fixed_cameras_and_no_major_open_issue(self):
        qa = json.loads((ROOT / "blender/buildings/bgc_building_0014/qa/discrepancies.json").read_text(encoding="utf-8"))
        self.assertEqual(len(qa["cameras"]), 5)
        self.assertEqual(qa["qa_refinement_passes"], 2)
        self.assertEqual(qa["critical_discrepancies_remaining"], 0)
        self.assertEqual(qa["major_discrepancies_remaining"], 0)

    def test_lod2_remains_reproducible(self):
        policy = json.loads((ROOT / "blender/buildings/bgc_building_0014/lod-policy.json").read_text(encoding="utf-8"))
        self.assertEqual(policy["lods"]["LOD2"]["status"], "PRESERVED_PROCEDURAL")
        self.assertIn("--central-square-lod2", policy["lods"]["LOD2"]["regeneration"])

    def test_unknowns_are_not_silently_promoted(self):
        summary = json.loads((ROOT / "data/reports/m7-summary.json").read_text(encoding="utf-8"))
        unknowns = set(summary["unknown_architectural_areas"])
        self.assertIn("east/service openings", unknowns)
        self.assertIn("roof equipment", unknowns)
        self.assertIn("exact entrances", unknowns)


if __name__ == "__main__":
    unittest.main()
