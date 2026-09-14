"""Semantic Central Square regression check; binary equality is intentionally excluded."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def within(value: float, limits: list[float]) -> bool:
    return limits[0] <= value <= limits[1]


def main() -> None:
    baseline = json.loads((ROOT / "data/reports/m8-central-square-regression-baseline.json").read_text(encoding="utf-8"))
    metrics = json.loads((ROOT / "data/reports/buildings/bgc_building_0014.json").read_text(encoding="utf-8"))
    build = json.loads((ROOT / "data/reports/buildings/bgc_building_0014-build.json").read_text(encoding="utf-8"))
    visual = json.loads((ROOT / "data/reports/visual-regression/bgc_building_0014/visual-regression.json").read_text(encoding="utf-8"))
    errors = []
    for axis, value in zip(("x", "y", "z"), metrics["dimensions_m"]):
        if not within(value, baseline["expected_dimensions_m"][f"{axis}_range"]):
            errors.append(f"{axis} dimension {value} outside baseline range")
    if not within(metrics["triangle_count"], baseline["triangle_range"]):
        errors.append("triangle count outside semantic range")
    if not within(metrics["mesh_count"], baseline["runtime_mesh_range"]):
        errors.append("runtime mesh count outside semantic range")
    if not within(metrics["file_size_bytes"], baseline["glb_size_bytes_range"]):
        errors.append("GLB size outside semantic range")
    if build["export"]["authoring_meshes"] != 25:
        errors.append("authoring component separation changed")
    if metrics.get("metadata_transport") != "PASS":
        errors.append("metadata transport failed")
    if visual.get("status") not in {"PASS", "WARNING"}:
        errors.append("visual regression failed")
    result = {
        "schema_version": 1,
        "status": "FAIL" if errors else "PASS",
        "binary_equality_required": False,
        "metrics": metrics,
        "visual_regression": visual["status"],
        "errors": errors,
    }
    output = ROOT / "data/reports/m8-central-square-regression.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"CENTRAL_SQUARE_REGRESSION: {result['status']} errors={len(errors)}")
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
