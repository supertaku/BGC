"""Generate an aerial diagnostic from a small set of real BGC OSM footprints."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import traceback


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from scene_tools import (
    add_camera,
    add_daylight,
    clear_scene,
    configure_scene,
    create_box,
    create_footprint_building,
    create_material,
    export_glb,
    render_png,
    save_blend,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data" / "processed" / "pilot-buildings.json"


def main() -> None:
    payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    buildings = payload["buildings"]
    if not buildings:
        raise RuntimeError("No normalized pilot buildings were found")
    clear_scene()
    configure_scene()
    verified_material = create_material("PilotVerifiedFootprint", (0.12, 0.34, 0.55, 1.0))
    estimated_material = create_material("PilotEstimatedHeight", (0.58, 0.35, 0.12, 1.0))
    procedural_material = create_material("PilotProceduralHeight", (0.42, 0.43, 0.46, 1.0))
    ground_material = create_material("PilotDiagnosticGround", (0.09, 0.12, 0.10, 1.0))

    all_points = [point for building in buildings for point in building["footprint"]]
    min_x, max_x = min(x for x, _ in all_points), max(x for x, _ in all_points)
    min_y, max_y = min(y for _, y in all_points), max(y for _, y in all_points)
    center_x, center_y = (min_x + max_x) / 2, (min_y + max_y) / 2
    extent = max(max_x - min_x, max_y - min_y, 80.0)
    create_box("PilotDiagnosticGround", (center_x, center_y, -0.1), (extent + 40, extent + 40, 0.2), ground_material)

    materials = {
        "VERIFIED_GEOGRAPHIC": verified_material,
        "ESTIMATED": estimated_material,
        "PROCEDURAL": procedural_material,
    }
    for building in buildings:
        height_observation = building["observations"]["height"]
        obj = create_footprint_building(
            building["id"].replace(":", "_"),
            building["footprint"],
            float(building["height"]),
            materials[height_observation["evidence_class"]],
        )
        obj["source_id"] = building["id"]
        obj["footprint_evidence"] = "verified geographic data"
        obj["height_evidence"] = height_observation["evidence_class"].lower()

    add_daylight()
    add_camera(
        "PilotAerialDiagnostic",
        (center_x + extent * 0.72, center_y - extent * 0.78, extent * 0.92),
        (center_x, center_y, 8.0),
        lens=52,
    )
    save_blend(ROOT / "blender" / "scenes" / "pilot-footprints.blend")
    render_png(ROOT / "blender" / "renders" / "pilot-footprints-aerial.png")
    export_glb(ROOT / "exports" / "glb" / "pilot-footprints.glb")
    print(f"BGC_PILOT: generated buildings={len(buildings)} source={SOURCE.name}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
