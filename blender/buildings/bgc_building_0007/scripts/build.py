"""Build, render, save, and export W Global Center LOD1."""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

import bpy


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[3]
for path in (ROOT, SCRIPT_DIR, ROOT / "blender" / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import scene_tools
import w_global
from blender.framework.export import export_runtime_glb
from blender.framework.qa import QACameraSpec, create_qa_cameras
from blender.framework.validation import validate_authoring_scene


BUILDING_DIR = ROOT / "blender" / "buildings" / w_global.ENTITY_ID
EXPORT = ROOT / "exports" / "glb" / "buildings" / f"{w_global.ENTITY_ID}_lod1.glb"
REPORT = ROOT / "data" / "reports" / "buildings" / f"{w_global.ENTITY_ID}-build.json"


def main() -> None:
    scene_tools.clear_scene()
    scene_tools.configure_scene()
    scene = bpy.context.scene
    scene["dataset_id"] = "w-global-center-lod1-m9"
    scene["entity_id"] = w_global.ENTITY_ID
    scene["horizontal_crs"] = "EPSG:32651"
    scene["units"] = "metres"
    scene["grounding_policy"] = "floor conflict preserved; weak sides conservative"
    scene.render.resolution_x = 960
    scene.render.resolution_y = 640
    meshes = w_global.build(scene_tools)

    ground_mat = scene_tools.create_material("WGC_QA_Ground", (0.16, 0.18, 0.17, 1.0), roughness=0.92)
    ground = scene_tools.create_box("WGC_DEBUG_QA_Ground", (97.8, 39.65, -0.2), (145.0, 145.0, 0.35), ground_mat)
    ground["exportable"] = False
    scene_tools.add_daylight()
    center = (97.8, 39.65, 14.0)
    cameras = [
        QACameraSpec("QA_30TH_01", "STREET_SIDE", (104.0, 150.0, 18.0), (104.0, 52.0, 14.0), 45.0, "qa-30th-01.png", "APPROXIMATE", ("ref:web:officepro-w-global",)),
        QACameraSpec("QA_9TH_01", "STREET_SIDE", (-5.0, 58.0, 18.0), (88.0, 43.0, 14.0), 45.0, "qa-9th-01.png", "APPROXIMATE", ("ref:web:officepro-w-global",)),
        QACameraSpec("QA_CORNER_01", "REFERENCE_MATCHED", (-5.0, 145.0, 22.0), (91.0, 57.0, 14.0), 48.0, "qa-corner-01.png", "APPROXIMATE", ("ref:web:officepro-w-global", "ref:web:colliers-w-global")),
        QACameraSpec("QA_WEAK_01", "DIAGNOSTIC", (162.0, -25.0, 18.0), center, 52.0, "qa-weak-01.png", "NOT_POSSIBLE_REFERENCE_MISSING"),
        QACameraSpec("QA_AERIAL_01", "AERIAL", (25.0, 115.0, 110.0), center, 55.0, "qa-aerial-01.png", "DIAGNOSTIC", ("ref:web:officepro-w-global",)),
    ]
    camera_records = create_qa_cameras(scene_tools, cameras, BUILDING_DIR / "renders" / "final")
    allowed = {slot.material for obj in meshes for slot in obj.material_slots if slot.material}
    validation = validate_authoring_scene(meshes, allowed)
    if validation["status"] == "FAIL":
        raise RuntimeError(f"authoring validation failed: {validation['errors']}")
    scene_tools.save_blend(BUILDING_DIR / "scenes" / "w-global-center-lod1.blend")
    merge_groups = {
        "WGC_30TH_WINDOWS": [f"wgc:window:30th-{index:02d}" for index in range(1, 25)],
        "WGC_9TH_WINDOWS": [f"wgc:window:9th-{index:02d}" for index in range(1, 33)],
        "WGC_GROUND_GLAZING": ["wgc:facade:30th-ground-glazing", "wgc:facade:9th-ground-glazing"],
        "WGC_OPEN_BAND_SLABS": [f"wgc:open-band:{side}-{band}-{part}" for side in ("30th", "9th") for band in (1, 2) for part in ("bottom_slab", "top_slab")],
        "WGC_OPEN_BAND_GUARDS": [f"wgc:open-band:{side}-{band}-guard_band" for side in ("30th", "9th") for band in (1, 2)],
        "WGC_OPEN_BAND_SHADOWS": [f"wgc:open-band:{side}-{band}-shadow" for side in ("30th", "9th") for band in (1, 2)],
        "WGC_DIAGONAL_BRACES": [f"wgc:structure:30th-brace-{index:02d}" for index in range(1, 3)] + [f"wgc:structure:9th-brace-{index:02d}" for index in range(1, 4)],
        "WGC_ROOF_FRAME": [f"wgc:roof:corner-frame-{index:02d}" for index in range(1, 4)],
    }
    export = export_runtime_glb(EXPORT, meshes, merge_groups)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({
        "schema_version": 1, "entity_id": w_global.ENTITY_ID, "status": "PASS",
        "authoring_validation": validation, "export": export,
        "qa_camera_count": len(camera_records), "materials_reused": 5,
        "shared_primitives": ["FacadeFrame", "OpenFacadeBand", "WindowGrid"],
        "floor_count_interpretation": "CONFLICTED_7_VS_8_VISIBLE_BANDS_MODELED",
    }, indent=2) + "\n", encoding="utf-8")
    print(f"WGC_BUILD: PASS authoring_meshes={len(meshes)} runtime_meshes={export['runtime_meshes']}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
