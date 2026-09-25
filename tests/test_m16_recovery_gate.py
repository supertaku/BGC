"""Evidence readiness must follow aspect and viewpoint review, not URL count."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/reconstruction"))
from evidence_gate import ASPECTS, assess  # noqa: E402


class EvidenceGateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.package = Path(self.tmp.name)
        self.data = {
            "entity_scope_status": "RESOLVED",
            "aspects": {key: {"rating": "PARTIAL", "basis": "reviewed source fact"}
                        for key in ASPECTS},
            "reconstruction_height_decision": {"height_m": 136, "source_ids": ["source:architect"],
                                               "conflict_retained": True},
            "viewpoints": [],
        }

    def write(self):
        (self.package / "evidence_coverage.json").write_text(json.dumps(self.data), encoding="utf-8")
        refs = {"records": [{"reference_id": item["reference_id"]} for item in self.data["viewpoints"]]}
        (self.package / "references.json").write_text(json.dumps(refs), encoding="utf-8")

    def test_two_urls_without_camera_matches_do_not_pass(self):
        self.data["viewpoints"] = [
            {"reference_id": f"ref:{i}", "camera_id": f"qa:{i}", "viewpoint_side": "WEST", "useful": True,
             "camera_match_confidence": .3} for i in range(2)]
        self.write()
        self.assertEqual(assess(self.package)["status"], "NOT_READY")

    def test_resolved_authoritative_height_conflict_can_pass(self):
        self.data["aspects"]["height"] = {"rating": "CONFLICTED", "basis": "OSM vs architect"}
        self.data["viewpoints"] = [
            {"reference_id": f"ref:{i}", "camera_id": f"qa:{i}", "viewpoint_side": side, "useful": True,
             "camera_match_confidence": .7} for i, side in enumerate(("WEST", "SOUTH"))]
        self.write()
        self.assertEqual(assess(self.package)["status"], "READY_FOR_VISUAL_RECONSTRUCTION")

    def test_unresolved_scope_blocks_ready_coverage(self):
        self.data["entity_scope_status"] = "UNRESOLVED"
        self.data["viewpoints"] = [
            {"reference_id": f"ref:{i}", "camera_id": f"qa:{i}", "viewpoint_side": side, "useful": True,
             "camera_match_confidence": .7} for i, side in enumerate(("WEST", "SOUTH"))]
        self.write()
        self.assertIn("entity scope unresolved", assess(self.package)["reasons"])


if __name__ == "__main__":
    unittest.main()
