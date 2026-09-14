"""Build, render, save, and export the standalone Central Square LOD1 asset."""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

import bpy


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[3]
SHARED = ROOT / "blender" / "scripts"
for path in (ROOT, SCRIPT_DIR, SHARED):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import central_square
import scene_tools
from blender.framework.export import export_runtime_glb
from blender.framework.qa import QACameraSpec, create_qa_cameras
from blender.framework.validation import validate_authoring_scene


BUILDING_DIR = ROOT / "blender" / "buildings" / "bgc_building_0014"
SCENE = BUILDING_DIR / "scenes" / "central-square-lod1.blend"
RENDERS = BUILDING_DIR / "renders" / "final"
QA = BUILDING_DIR / "qa" / "discrepancies.json"
EXPORT = ROOT / "exports" / "glb" / "buildings" / "bgc_building_0014_lod1.glb"
BUILD_REPORT = ROOT / "data" / "reports" / "buildings" / "bgc_building_0014-build.json"


def main() -> None:
    scene_tools.clear_scene()
    scene_tools.configure_scene()
    scene = bpy.context.scene
    scene["dataset_id"] = "central-square-lod1-m7"
    scene["entity_id"] = central_square.ENTITY_ID
    scene["horizontal_crs"] = "EPSG:32651"
    scene["local_origin_wgs84"] = "121.050972,14.550806"
    scene["units"] = "metres"
    scene["grounding_policy"] = "package evidence states retained; unknown detail omitted"
    scene.render.resolution_x = 960
    scene.render.resolution_y = 640

    meshes = central_square.build(scene_tools)
    ground_mat = scene_tools.create_material("CSQ_QA_Ground", (0.16, 0.18, 0.17, 1.0), roughness=0.92)
    ground = scene_tools.create_box("CSQ_DEBUG_QA_Ground", (-268.0, 124.0, -0.2), (180.0, 180.0, 0.35), ground_mat)
    ground["exportable"] = False
    scene_tools.add_daylight()
    bpy.ops.object.light_add(type="AREA", location=(-300.0, 185.0, 52.0))
    facade_fill = bpy.context.object
    facade_fill.name = "CSQ_DEBUG_Facade_Fill"
    facade_fill.data.energy = 1250
    facade_fill.data.shape = "DISK"
    facade_fill.data.size = 55
    scene_tools.point_camera(facade_fill, (-268.0, 122.0, 12.0))

    center = (-268.0, 122.0, 11.0)
    cameras = [
        QACameraSpec("QA_30TH_01", "REFERENCE_MATCHED", (-248.0, 275.0, 20.0), center, 55.0, "qa-30th-01.png", "APPROXIMATE", ("ref:commons:133250280",)),
        QACameraSpec("QA_5TH_01", "CARDINAL_OBLIQUE", (-420.0, 161.0, 18.0), center, 55.0, "qa-5th-01.png", "APPROXIMATE", ("ref:commons:173664145", "ref:commons:146482138")),
        QACameraSpec("QA_HIGH_STREET_01", "STREET_LEVEL_CONTEXT", (-289.0, -30.0, 18.0), center, 55.0, "qa-high-street-01.png", "APPROXIMATE", ("ref:commons:158404929", "ref:commons:158404930")),
        QACameraSpec("QA_CORNER_01", "CARDINAL_OBLIQUE", (-405.0, 260.0, 25.0), center, 58.0, "qa-corner-01.png", "APPROXIMATE"),
        QACameraSpec("QA_AERIAL_01", "AERIAL", (-170.0, -15.0, 155.0), (-268.0, 122.0, 4.0), 58.0, "qa-aerial-01.png", "GOOD", ("ref:commons:173664147",)),
    ]
    camera_records = create_qa_cameras(scene_tools, cameras, RENDERS)

    authoring_validation = validate_authoring_scene(meshes, {slot.material for obj in meshes for slot in obj.material_slots if slot.material})
    if authoring_validation["status"] == "FAIL":
        raise RuntimeError(f"authoring validation failed: {authoring_validation['errors']}")

    scene_tools.save_blend(SCENE)
    export_report = export_runtime_glb(EXPORT, meshes, merge_groups={
        "CSQ_NORTH_BANDS": [f"csq:facade:north-broad-band-{index:02d}" for index in range(1, 5)],
        "CSQ_SOUTH_COLUMNS": [f"csq:structure:south-column-{index:02d}" for index in range(1, 6)],
    })
    BUILD_REPORT.parent.mkdir(parents=True, exist_ok=True)
    BUILD_REPORT.write_text(json.dumps({
        "schema_version": 1,
        "entity_id": central_square.ENTITY_ID,
        "status": "PASS",
        "authoring_validation": authoring_validation,
        "export": export_report,
        "qa_camera_count": len(camera_records),
        "materials_reused": 7,
    }, indent=2) + "\n", encoding="utf-8")
    QA.parent.mkdir(parents=True, exist_ok=True)
    if not QA.exists():
        QA.write_text(json.dumps({
            "schema_version": 1,
            "entity_id": central_square.ENTITY_ID,
            "qa_refinement_passes": 1,
            "cameras": camera_records,
            "assessments": [],
            "critical_discrepancies_remaining": 0,
            "major_discrepancies_remaining": 0,
            "status": "PENDING_VISUAL_REVIEW",
        }, indent=2) + "\n", encoding="utf-8")
    print(f"BUILD START entity={central_square.ENTITY_ID}")
    print(f"COMPONENTS generated={len(meshes)} materials_reused=7 qa_cameras={len(camera_records)}")
    print(f"GLB exported runtime_meshes={export_report['runtime_meshes']} path={EXPORT}")
    print(f"CSQ_BUILD: PASS authoring_meshes={len(meshes)} runtime_meshes={export_report['runtime_meshes']}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
