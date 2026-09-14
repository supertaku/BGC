"""Re-import validation for the standalone Central Square LOD1 GLB."""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[4]
GLB = ROOT / "exports" / "glb" / "buildings" / "bgc_building_0014_lod1.glb"
METRICS = ROOT / "exports" / "glb" / "buildings" / "bgc_building_0014_lod1.metrics.json"
REPORT_METRICS = ROOT / "data" / "reports" / "buildings" / "bgc_building_0014.json"


def main() -> None:
    if not GLB.is_file() or GLB.stat().st_size == 0:
        raise RuntimeError(f"Missing GLB: {GLB}")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(GLB))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("GLB contains no meshes")
    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    bounds = {
        "min": [round(min(point[i] for point in points), 3) for i in range(3)],
        "max": [round(max(point[i] for point in points), 3) for i in range(3)],
    }
    dimensions = [bounds["max"][i] - bounds["min"][i] for i in range(3)]
    triangles = sum(len(obj.data.loop_triangles) or len(obj.data.polygons) for obj in meshes)
    for obj in meshes:
        obj.data.calc_loop_triangles()
    triangles = sum(len(obj.data.loop_triangles) for obj in meshes)
    materials = {slot.material.name for obj in meshes for slot in obj.material_slots if slot.material}
    vertices = sum(len(obj.data.vertices) for obj in meshes)
    textures = {image.name for image in bpy.data.images if image.source != "VIEWER"}
    entity_ids = {obj.get("entity_id") for obj in meshes if obj.get("entity_id")}
    metadata_missing = [
        obj.name for obj in meshes
        if not all(obj.get(key) is not None for key in (
            "entity_id", "component_id", "component_type", "evidence_status",
            "observation_ids", "reconstruction_fidelity",
        ))
    ]
    if not (24.8 <= dimensions[2] <= 26.2):
        raise RuntimeError(f"Unexpected height after import: {dimensions[2]:.3f} m")
    if bounds["min"][0] > -310 or bounds["max"][0] < -230 or bounds["min"][1] > 90 or bounds["max"][1] < 150:
        raise RuntimeError(f"Geographic placement check failed: {bounds}")
    if len(materials) < 5:
        raise RuntimeError(f"Material survival check failed: {len(materials)}")
    if entity_ids != {"bgc_building_0014"}:
        raise RuntimeError(f"GLB entity metadata mismatch: {sorted(entity_ids)}")
    if metadata_missing:
        raise RuntimeError(f"GLB nodes missing compact component metadata: {metadata_missing}")
    metrics = {
        "schema_version": 1,
        "file": str(GLB),
        "file_size_bytes": GLB.stat().st_size,
        "mesh_count": len(meshes),
        "object_count": len(meshes),
        "vertex_count": vertices,
        "triangle_count": triangles,
        "material_count": len(materials),
        "texture_count": len(textures),
        "instance_count": sum(1 for obj in meshes if obj.type == "MESH" and obj.data.users > 1),
        "draw_call_approximation": sum(max(1, len(obj.material_slots)) for obj in meshes),
        "bounds_m": bounds,
        "dimensions_m": [round(value, 3) for value in dimensions],
        "geographic_placement": "PASS",
        "height_validation": "PASS",
        "materials_survive": "PASS",
        "metadata_transport": "PASS",
        "entity_id": "bgc_building_0014",
        "validation": "PASS",
    }
    METRICS.parent.mkdir(parents=True, exist_ok=True)
    METRICS.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    REPORT_METRICS.parent.mkdir(parents=True, exist_ok=True)
    REPORT_METRICS.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(f"CSQ_VALIDATE: PASS size={GLB.stat().st_size} meshes={len(meshes)} triangles={triangles} materials={len(materials)} bounds={bounds}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
