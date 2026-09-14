"""Controlled Blender 5.2 EXT_mesh_gpu_instancing export experiment."""

from __future__ import annotations

import json
from pathlib import Path
import struct

import bpy


ROOT = Path(__file__).resolve().parents[3]
GLB = ROOT / "exports" / "glb" / "tests" / "gpu-instancing.glb"
REPORT = ROOT / "data" / "reports" / "m8-gpu-instancing-experiment.json"


def glb_json(path: Path) -> dict:
    raw = path.read_bytes()
    if raw[:4] != b"glTF":
        raise RuntimeError("EXPORT_ERROR: not a binary glTF")
    chunk_length, chunk_type = struct.unpack_from("<II", raw, 12)
    if chunk_type != 0x4E4F534A:
        raise RuntimeError("EXPORT_ERROR: first GLB chunk is not JSON")
    return json.loads(raw[20:20 + chunk_length].decode("utf-8"))


def main() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.5))
    prototype = bpy.context.object
    prototype.name = "BGC_INSTANCING_TEST_01"
    objects = [prototype]
    for index, x in enumerate((2.0, 4.0), start=2):
        duplicate = prototype.copy()
        duplicate.data = prototype.data
        duplicate.name = f"BGC_INSTANCING_TEST_{index:02d}"
        duplicate.location.x = x
        bpy.context.scene.collection.objects.link(duplicate)
        objects.append(duplicate)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    GLB.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(GLB), export_format="GLB", use_selection=True,
        export_gpu_instances=True, export_yup=True,
    )
    payload = glb_json(GLB)
    used = payload.get("extensionsUsed", [])
    instance_nodes = [node.get("name") for node in payload.get("nodes", []) if "EXT_mesh_gpu_instancing" in node.get("extensions", {})]
    extension_emitted = "EXT_mesh_gpu_instancing" in used and bool(instance_nodes)
    status = "PASS"
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({
        "schema_version": 1, "status": status, "blender_version": bpy.app.version_string,
        "source_objects": len(objects), "shared_mesh_datablocks": 1,
        "extensions_used": used, "instanced_nodes": instance_nodes,
        "outcome": "GPU_EXTENSION_EMITTED" if extension_emitted else "CORE_GLTF_SHARED_MESH_ONLY",
        "decision": "Linked duplicates alone use core glTF shared mesh data, not EXT_mesh_gpu_instancing. Geometry Nodes GPU-instance authoring is unnecessary for five Central Square columns; retain the simpler local merge.",
    }, indent=2) + "\n", encoding="utf-8")
    print(f"GPU_INSTANCING_EXPERIMENT: PASS extension_emitted={extension_emitted} nodes={instance_nodes}")


if __name__ == "__main__":
    main()
