"""Authoring-scene invariants checked before runtime export."""

from __future__ import annotations

import re

from blender.framework.materials.library import duplicate_material_groups


BAD_DEFAULT_NAME = re.compile(r"^(Cube|Plane|Cylinder|Sphere)(\.\d+)?$")


def validate_authoring_scene(objects, materials) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    names = [obj.name for obj in objects]
    if len(names) != len(set(names)):
        errors.append("duplicate production object names")
    unacceptable = sorted(name for name in names if BAD_DEFAULT_NAME.match(name))
    if unacceptable:
        errors.append(f"unacceptable Blender default names: {unacceptable}")
    component_ids = [obj.get("component_id") for obj in objects]
    missing_components = [obj.name for obj in objects if not obj.get("component_id")]
    if missing_components:
        errors.append(f"objects missing component_id: {missing_components}")
    duplicates = sorted({item for item in component_ids if item and component_ids.count(item) > 1})
    if duplicates:
        errors.append(f"duplicate component IDs: {duplicates}")
    for obj in objects:
        state = obj.get("evidence_status")
        if not state:
            errors.append(f"{obj.name}: missing evidence_status")
        if isinstance(state, str) and state.startswith("VERIFIED") and obj.get("observation_ids") in (None, "[]"):
            errors.append(f"{obj.name}: verified component has no observation_ids")
        if state == "UNKNOWN" and len(getattr(obj.data, "polygons", [])) > 24:
            warnings.append(f"{obj.name}: detailed UNKNOWN geometry requires review")
    duplicate_materials = duplicate_material_groups(materials)
    if duplicate_materials:
        warnings.append(f"materially identical duplicate definitions: {duplicate_materials}")
    return {"status": "FAIL" if errors else ("WARNING" if warnings else "PASS"), "errors": errors, "warnings": warnings}

