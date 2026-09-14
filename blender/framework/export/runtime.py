"""Create an optimized temporary runtime representation and export it to GLB."""

from __future__ import annotations

import json
from pathlib import Path

import bpy


def _copy_runtime_object(source, name: str):
    clone = source.copy()
    clone.data = source.data.copy()
    clone.name = name
    clone.parent = None
    bpy.context.scene.collection.objects.link(clone)
    return clone


def _merge_objects(sources, name: str, component_type: str):
    materials = {slot.material for source in sources for slot in source.material_slots if slot.material}
    if len(materials) != 1:
        raise ValueError(f"runtime merge group {name} must use exactly one material")
    vertices = []
    faces = []
    for source in sources:
        offset = len(vertices)
        vertices.extend(tuple(source.matrix_world @ vertex.co) for vertex in source.data.vertices)
        faces.extend(tuple(offset + index for index in polygon.vertices) for polygon in source.data.polygons)
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.validate(clean_customdata=True)
    mesh.update()
    merged = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(merged)
    merged.data.materials.append(next(iter(materials)))
    first = sources[0]
    for key in ("entity_id", "evidence_status", "reconstruction_fidelity", "target_time_state"):
        if first.get(key) is not None:
            merged[key] = first[key]
    merged["component_id"] = f"runtime:{component_type}"
    merged["component_ids"] = json.dumps([obj.get("component_id") for obj in sources], separators=(",", ":"))
    merged["component_type"] = component_type
    merged["observation_ids"] = json.dumps(sorted({item for obj in sources for item in json.loads(obj.get("observation_ids", "[]"))}), separators=(",", ":"))
    merged["evidence_ids"] = json.dumps(sorted({item for obj in sources for item in json.loads(obj.get("evidence_ids", "[]"))}), separators=(",", ":"))
    merged["exportable"] = True
    return merged


def export_runtime_glb(path: Path, objects, merge_groups: dict[str, list[str]] | None = None) -> dict:
    """Export selected authoring objects, merging only explicit safe groups."""
    path.parent.mkdir(parents=True, exist_ok=True)
    by_component = {obj.get("component_id"): obj for obj in objects}
    consumed: set[str] = set()
    runtime = []
    for group_name, component_ids in (merge_groups or {}).items():
        missing = sorted(set(component_ids) - set(by_component))
        if missing:
            raise ValueError(f"runtime merge group {group_name} has unknown components: {missing}")
        sources = [by_component[item] for item in component_ids]
        runtime.append(_merge_objects(sources, f"BGC_RUNTIME_{group_name}", group_name.lower()))
        consumed.update(component_ids)
    for index, source in enumerate(objects, start=1):
        if source.get("component_id") not in consumed:
            runtime.append(_copy_runtime_object(source, f"BGC_RUNTIME_{index:03d}_{source.name}"))
    bpy.ops.object.select_all(action="DESELECT")
    for obj in runtime:
        obj.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=str(path), export_format="GLB", use_selection=True,
        export_yup=True, export_apply=True, export_extras=True,
    )
    for obj in runtime:
        mesh = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    return {
        "authoring_meshes": len(objects),
        "runtime_meshes": len(runtime),
        "merged_meshes": len(objects) - len(runtime),
        "path": str(path),
    }


def merge_runtime_in_place(objects, merge_groups: dict[str, list[str]]):
    """Replace explicit safe groups in a disposable integration scene."""
    by_component = {obj.get("component_id"): obj for obj in objects}
    consumed = set()
    merged = []
    for group_name, component_ids in merge_groups.items():
        sources = [by_component[item] for item in component_ids]
        merged.append(_merge_objects(sources, f"BGC_RUNTIME_{group_name}", group_name.lower()))
        consumed.update(component_ids)
    kept = [obj for obj in objects if obj.get("component_id") not in consumed]
    for source in objects:
        if source.get("component_id") in consumed:
            mesh = source.data
            bpy.data.objects.remove(source, do_unlink=True)
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)
    return kept + merged
