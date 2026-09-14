"""Import the generated GLB into a clean scene and assert useful content."""

from pathlib import Path
import argparse
import json
import sys
import traceback

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import bpy
from mathutils import Vector

from scene_tools import clear_scene


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GLB = ROOT / "exports" / "glb" / "integration-test.glb"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=DEFAULT_GLB)
    parser.add_argument("--metrics", type=Path)
    parser.add_argument("--entity-id")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    glb = args.path.resolve()
    if not glb.is_file() or glb.stat().st_size == 0:
        raise RuntimeError(f"Missing or empty GLB: {glb}")
    clear_scene()
    bpy.ops.import_scene.gltf(filepath=str(glb))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    for obj in meshes:
        obj.data.calc_loop_triangles()
    polygons = sum(len(obj.data.loop_triangles) for obj in meshes)
    vertices = sum(len(obj.data.vertices) for obj in meshes)
    materials = {slot.material.name for obj in meshes for slot in obj.material_slots if slot.material}
    if not meshes or polygons == 0 or not materials:
        raise RuntimeError(f"Invalid GLB content: meshes={len(meshes)}, polygons={polygons}, materials={len(materials)}")
    dimensions = [component for obj in meshes for component in obj.dimensions]
    if max(dimensions, default=0) < 10 or max(dimensions, default=0) > 1000:
        raise RuntimeError(f"Unexpected model scale: maximum object dimension {max(dimensions, default=0):.3f}")
    world_points = []
    for obj in meshes:
        for corner in obj.bound_box:
            world_points.append(obj.matrix_world @ Vector(corner))
    bounds = {
        "min": [round(min(point[index] for point in world_points), 3) for index in range(3)],
        "max": [round(max(point[index] for point in world_points), 3) for index in range(3)],
    }
    metrics = {
        "schema_version": 1,
        "entity_id": args.entity_id,
        "file": str(glb),
        "file_size_bytes": glb.stat().st_size,
        "mesh_count": len(meshes),
        "triangle_count": polygons,
        "vertex_count": vertices,
        "material_count": len(materials),
        "draw_call_approximation": sum(max(1, len(obj.material_slots)) for obj in meshes),
        "runtime_node_count": len(meshes),
        "bounds_m": bounds,
        "maximum_object_dimension_m": round(max(dimensions), 3),
        "validation": "PASS",
    }
    if args.metrics:
        metrics_path = args.metrics.resolve()
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        metrics_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(
        f"BGC_GLB: PASS file={glb.name} size_bytes={metrics['file_size_bytes']} "
        f"meshes={len(meshes)} triangles={polygons} materials={len(materials)} "
        f"draw_calls_approx={metrics['draw_call_approximation']} max_dimension_m={max(dimensions):.3f}"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
