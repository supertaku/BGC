"""Conservative, explicit M16R visual-reconstruction readiness check.

Coverage is authored after inspecting an aspect; reference counts never imply
coverage. This module is dependency-free so it can run before Blender.
"""

from __future__ import annotations

import json
from pathlib import Path


ASPECTS = (
    "identity", "footprint", "height", "massing", "principal_facade",
    "secondary_facade", "roof", "entrance", "materials",
)
RATINGS = {"GOOD", "PARTIAL", "WEAK", "NONE", "CONFLICTED"}
REQUIRED = ("identity", "footprint", "height", "massing", "principal_facade")


def assess(package: Path) -> dict:
    path = package / "evidence_coverage.json"
    if not path.exists():
        return {"status": "NOT_READY", "reasons": ["No explicit evidence_coverage.json review"]}
    data = json.loads(path.read_text(encoding="utf-8"))
    reasons = []
    aspects = data.get("aspects", {})
    for aspect in ASPECTS:
        entry = aspects.get(aspect)
        if not isinstance(entry, dict) or entry.get("rating") not in RATINGS:
            reasons.append(f"{aspect}: missing explicit coverage rating")
            continue
        decided_conflict = (aspect == "height" and entry["rating"] == "CONFLICTED"
                            and data.get("reconstruction_height_decision", {}).get("conflict_retained")
                            and data.get("reconstruction_height_decision", {}).get("source_ids"))
        if aspect in REQUIRED and entry["rating"] not in {"GOOD", "PARTIAL"} and not decided_conflict:
            reasons.append(f"{aspect}: {entry['rating']} is insufficient")
        if aspect in REQUIRED and not entry.get("basis"):
            reasons.append(f"{aspect}: missing evidence basis")
    if not data.get("reconstruction_height_decision", {}).get("source_ids"):
        reasons.append("height: missing reconstruction decision provenance")
    views = data.get("viewpoints", [])
    refs_path = package / "references.json"
    known_refs = {item.get("reference_id") for item in json.loads(refs_path.read_text(encoding="utf-8")).get("records", [])} if refs_path.exists() else set()
    spec_path = package / "reconstruction_spec.json"
    cameras = {}
    if spec_path.exists():
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        cameras = {item.get("camera_id"): item for item in spec.get("visual_qa_cameras", [])}
    for view in views:
        if view.get("reference_id") not in known_refs:
            reasons.append(f"viewpoint references unknown record: {view.get('reference_id')}")
        if cameras and cameras.get(view.get("camera_id"), {}).get("corresponding_reference") != view.get("reference_id"):
            reasons.append(f"viewpoint lacks one-to-one QA camera: {view.get('reference_id')}")
    useful = [view for view in views if view.get("useful") is True
              and view.get("reference_id") in known_refs
              and view.get("camera_id")
              and view.get("viewpoint_side") not in {None, "", "UNRESOLVED"}
              and view.get("camera_match_confidence", 0) >= 0.5]
    if len({view["reference_id"] for view in useful}) < 2:
        reasons.append("fewer than two inspected, camera-matchable viewpoints")
    if data.get("entity_scope_status") != "RESOLVED":
        reasons.append("entity scope unresolved")
    return {"status": "READY_FOR_VISUAL_RECONSTRUCTION" if not reasons else "NOT_READY",
            "reasons": reasons, "coverage": aspects, "useful_viewpoints": len(useful)}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    args = parser.parse_args()
    result = assess(args.package)
    print(json.dumps(result, indent=2))
    raise SystemExit(result["status"] != "READY_FOR_VISUAL_RECONSTRUCTION")
