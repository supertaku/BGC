"""Small deterministic material family library for web-delivered LOD assets."""

from __future__ import annotations


MATERIAL_FAMILIES = {
    "warm_neutral_cladding": ("BGC_MAT_WARM_NEUTRAL_CLADDING_01", (0.52, 0.40, 0.28, 1.0), 0.68, 0.0),
    "light_neutral_panel": ("BGC_MAT_LIGHT_NEUTRAL_PANEL_01", (0.73, 0.71, 0.66, 1.0), 0.72, 0.0),
    "architectural_dark_glass": ("BGC_MAT_ARCHITECTURAL_DARK_GLASS_01", (0.035, 0.075, 0.09, 1.0), 0.28, 0.05),
    "generic_storefront_glass": ("BGC_MAT_STOREFRONT_GLASS_01", (0.07, 0.13, 0.15, 1.0), 0.22, 0.04),
    "dark_metal": ("BGC_MAT_DARK_METAL_01", (0.045, 0.05, 0.055, 1.0), 0.32, 0.72),
    "neutral_roof": ("BGC_MAT_NEUTRAL_ROOF_01", (0.60, 0.61, 0.58, 1.0), 0.86, 0.0),
    "generic_placeholder": ("BGC_MAT_GENERIC_PLACEHOLDER_01", (0.10, 0.16, 0.19, 1.0), 0.50, 0.0),
}


def create_material_family(scene_tools, family: str):
    try:
        name, color, roughness, metallic = MATERIAL_FAMILIES[family]
    except KeyError as exc:
        raise ValueError(f"unknown shared material family: {family}") from exc
    material = scene_tools.create_material(name, color, roughness=roughness, metallic=metallic)
    material["material_family"] = family
    material["web_pbr"] = "glTF metallic-roughness / Principled BSDF"
    return material


def material_signature(material) -> tuple:
    principled = material.node_tree.nodes.get("Principled BSDF") if material.use_nodes else None
    if not principled:
        return (tuple(round(v, 5) for v in material.diffuse_color),)
    color = tuple(round(v, 5) for v in principled.inputs["Base Color"].default_value)
    roughness = round(float(principled.inputs["Roughness"].default_value), 5)
    metallic_input = principled.inputs.get("Metallic") or principled.inputs.get("Metallic IOR Level")
    metallic = round(float(metallic_input.default_value), 5) if metallic_input else 0.0
    return color, roughness, metallic


def duplicate_material_groups(materials) -> list[list[str]]:
    by_signature: dict[tuple, list[str]] = {}
    for material in materials:
        by_signature.setdefault(material_signature(material), []).append(material.name)
    return [sorted(names) for names in by_signature.values() if len(names) > 1]

