"""Evidence-grounded, deterministic Central Square LOD1 construction helpers."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Iterable

import bpy

from blender.framework.materials import create_material_family
from blender.framework.metadata import apply_component_metadata


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = ROOT / "data" / "reconstruction_packages" / "bgc_building_0014"

ENTITY_ID = "bgc_building_0014"
HEIGHT_M = 25.9
ANGLE_DEG = -17.279
ANGLE = math.radians(ANGLE_DEG)
U = (math.cos(ANGLE), math.sin(ANGLE))
V = (-math.sin(ANGLE), math.cos(ANGLE))
SOURCE_IDS = {
    "osm:way:205968610",
    "osm:way:470203065",
    "osm:way:470203066",
    "osm:way:470203067",
}


def _load(name: str) -> dict:
    return json.loads((PACKAGE / name).read_text(encoding="utf-8"))


def _ring(feature: dict) -> list[list[float]]:
    ring = feature["geometry"]["coordinates"][0]
    return ring[:-1] if ring and ring[0] == ring[-1] else ring


def _centroid(points: list[list[float]]) -> tuple[float, float]:
    twice_area = 0.0
    cx = 0.0
    cy = 0.0
    for index, (x1, y1) in enumerate(points):
        x2, y2 = points[(index + 1) % len(points)]
        cross = x1 * y2 - x2 * y1
        twice_area += cross
        cx += (x1 + x2) * cross
        cy += (y1 + y2) * cross
    return cx / (3.0 * twice_area), cy / (3.0 * twice_area)


def _project(point: tuple[float, float], origin: tuple[float, float], axis: tuple[float, float]) -> float:
    return (point[0] - origin[0]) * axis[0] + (point[1] - origin[1]) * axis[1]


def _create_empty(name: str, parent: bpy.types.Object | None = None) -> bpy.types.Object:
    obj = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = parent
    return obj


def _tag(
    obj: bpy.types.Object,
    component_id: str,
    evidence_status: str,
    observation_ids: Iterable[str],
    evidence_ids: Iterable[str] = (),
) -> bpy.types.Object:
    component_type = component_id.split(":", 2)[1] if ":" in component_id else "architectural_component"
    tagged = apply_component_metadata(
        obj,
        entity_id=ENTITY_ID,
        component_id=component_id,
        component_type=component_type,
        evidence_status=evidence_status,
        observation_ids=observation_ids,
        evidence_ids=evidence_ids,
        reconstruction_fidelity="LOD1_MEDIUM_ARCHITECTURAL_FIDELITY",
        target_time_state="CURRENT_APPROX_2025_2026",
    )
    tagged["lod"] = "LOD1"
    return tagged


def _oriented_box(
    scene_tools,
    name: str,
    center: tuple[float, float],
    dimensions: tuple[float, float, float],
    z: float,
    material,
    parent,
    component_id: str,
    status: str,
    observations: Iterable[str],
    evidence: Iterable[str] = (),
):
    obj = scene_tools.create_box(name, (center[0], center[1], z), dimensions, material)
    obj.rotation_euler[2] = ANGLE
    obj.parent = parent
    return _tag(obj, component_id, status, observations, evidence)


def _point(origin: tuple[float, float], u: float, v: float) -> tuple[float, float]:
    return (origin[0] + U[0] * u + V[0] * v, origin[1] + U[1] * u + V[1] * v)


def build(scene_tools, parent: bpy.types.Object | None = None) -> list[bpy.types.Object]:
    """Build LOD1 into the current scene and return exportable mesh objects."""
    geometry = _load("geometry.geojson")
    features = {feature["properties"]["id"]: feature for feature in geometry["features"]}
    main_feature = features["osm:way:470203066"]
    main_ring = _ring(main_feature)
    origin = _centroid(main_ring)
    u_values = [_project(tuple(point), origin, U) for point in main_ring]
    v_values = [_project(tuple(point), origin, V) for point in main_ring]
    u_min, u_max = min(u_values), max(u_values)
    v_min, v_max = min(v_values), max(v_values)
    u_span, v_span = u_max - u_min, v_max - v_min

    root = _create_empty("CSQ_ROOT", parent)
    root["entity_id"] = ENTITY_ID
    root["coordinate_frame"] = "BGC local metres: X east, Y north, Z up"
    root["height_m"] = HEIGHT_M
    root["height_status"] = "VERIFIED_GEOGRAPHIC_NOT_SURVEYED"
    root["source_package"] = "data/reconstruction_packages/bgc_building_0014"
    root["lod"] = "LOD1"

    groups = {
        name: _create_empty(f"CSQ_{name}", root)
        for name in (
            "MASSING", "MAJOR_VOLUMES", "FACADE_30TH", "FACADE_5TH",
            "FACADE_HIGH_STREET", "FACADE_OTHER", "ENTRANCES", "GLAZING",
            "CLADDING", "STRUCTURAL_ELEMENTS", "ROOF", "SIGNAGE_PLACEHOLDERS", "DEBUG",
        )
    }

    mats = {
        "warm": create_material_family(scene_tools, "warm_neutral_cladding"),
        "light": create_material_family(scene_tools, "light_neutral_panel"),
        "dark_glass": create_material_family(scene_tools, "architectural_dark_glass"),
        "storefront": create_material_family(scene_tools, "generic_storefront_glass"),
        "metal": create_material_family(scene_tools, "dark_metal"),
        "roof": create_material_family(scene_tools, "neutral_roof"),
        "display": create_material_family(scene_tools, "generic_placeholder"),
    }

    meshes: list[bpy.types.Object] = []
    main = scene_tools.create_extruded_polygons(
        "CSQ_MASSING_Main_Volume",
        [main_feature["geometry"]["coordinates"]],
        0.0,
        HEIGHT_M,
        mats["warm"],
        "verified geographic footprint; evidence-linked geographic height",
    )
    main.parent = groups["MASSING"]
    meshes.append(_tag(main, "csq:massing:main-volume", "VERIFIED_GEOGRAPHIC", ["obs:csq:footprint-area", "obs:csq:height", "obs:csq:dominant-massing"], ["source:osm", "ref:commons:133250280", "ref:commons:173664147"]))

    for source_id, name, component_id, status, parent_name in (
        ("osm:way:470203065", "CSQ_MASSING_Northwest_Column", "csq:massing:northwest-column", "VERIFIED_GEOGRAPHIC", "STRUCTURAL_ELEMENTS"),
        ("osm:way:470203067", "CSQ_MASSING_Northeast_Column", "csq:massing:northeast-column", "ESTIMATED", "STRUCTURAL_ELEMENTS"),
    ):
        feature = features[source_id]
        obj = scene_tools.create_extruded_polygons(
            name, [feature["geometry"]["coordinates"]], 0.0,
            float(feature["properties"]["height_m"]), mats["metal"],
            "verified geographic part footprint with evidence-classified height",
        )
        obj.parent = groups[parent_name]
        meshes.append(_tag(obj, component_id, status, ["obs:csq:height-audit"], ["source:osm"]))

    # North / 30th Street: strong evidence, few large openings rather than a false fine grid.
    north_v = v_max + 0.10
    meshes.append(_oriented_box(scene_tools, "CSQ_FACADE_30TH_Ground_Storefront", _point(origin, 0, north_v), (u_span * 0.83, 0.24, 4.25), 2.45, mats["storefront"], groups["FACADE_30TH"], "csq:facade:north-ground-retail", "VERIFIED_PHOTOGRAPHIC", ["obs:csq:north-facade"], ["ref:commons:133250280"]))
    for index, (u_pos, width, height, base) in enumerate(((-25.0, 9.5, 17.2, 5.5), (1.5, 7.0, 19.0, 4.7), (25.0, 10.5, 15.5, 7.0)), start=1):
        meshes.append(_oriented_box(scene_tools, f"CSQ_FACADE_30TH_Glazed_Zone_{index:02d}", _point(origin, u_pos, north_v + 0.02), (width, 0.28, height), base + height / 2, mats["dark_glass"], groups["FACADE_30TH"], f"csq:facade:north-glazed-zone-{index:02d}", "VERIFIED_PHOTOGRAPHIC", ["obs:csq:north-facade"], ["ref:commons:133250280"]))
    for index, z in enumerate((8.0, 13.0, 18.0, 23.0), start=1):
        meshes.append(_oriented_box(scene_tools, f"CSQ_FACADE_30TH_Broad_Band_{index:02d}", _point(origin, 2.0, north_v + 0.08), (u_span * 0.66, 0.16, 0.22), z, mats["metal"], groups["FACADE_30TH"], f"csq:facade:north-broad-band-{index:02d}", "ESTIMATED", ["obs:csq:above-ground-storeys", "obs:csq:north-facade"], ["ref:commons:133250280"]))
    meshes.append(_oriented_box(scene_tools, "CSQ_SIGNAGE_Northwest_Neutral_Display", _point(origin, u_min + 10.5, north_v + 0.05), (13.0, 0.32, 7.6), 13.3, mats["display"], groups["SIGNAGE_PLACEHOLDERS"], "csq:signage:northwest-placeholder", "PROCEDURAL", ["obs:csq:north-facade"], ["ref:commons:133250280"]))

    # West / 5th Avenue: partial coverage, one broad vertical cut and an understated inferred portal.
    west_u = u_min - 0.10
    meshes.append(_oriented_box(scene_tools, "CSQ_FACADE_5TH_Ground_Storefront", _point(origin, west_u, 0), (0.24, v_span * 0.78, 4.25), 2.45, mats["storefront"], groups["FACADE_5TH"], "csq:facade:west-ground-retail", "VERIFIED_PHOTOGRAPHIC", ["obs:csq:west-facade"], ["ref:commons:173664145", "ref:commons:146482138"]))
    meshes.append(_oriented_box(scene_tools, "CSQ_FACADE_5TH_Tall_Glazed_Bay", _point(origin, west_u - 0.02, 7.0), (0.28, 11.0, 18.0), 14.4, mats["dark_glass"], groups["FACADE_5TH"], "csq:facade:west-tall-glazed-bay", "INFERRED", ["obs:csq:west-facade"], ["ref:commons:173664145", "ref:commons:146482138"]))
    meshes.append(_oriented_box(scene_tools, "CSQ_ENTRANCE_5TH_01", _point(origin, west_u - 0.07, -9.0), (0.38, 8.0, 4.6), 2.3, mats["dark_glass"], groups["ENTRANCES"], "csq:entrance:west-public-approach", "INFERRED", ["obs:csq:public-approach"], ["ref:youtube:tour-from-home-central-square-2021", "ref:youtube:hg-central-square-2023"]))
    meshes.append(_oriented_box(scene_tools, "CSQ_ENTRANCE_5TH_Canopy_Placeholder", _point(origin, west_u - 1.25, -9.0), (2.7, 9.0, 0.35), 4.75, mats["metal"], groups["ENTRANCES"], "csq:entrance:west-canopy-placeholder", "ESTIMATED", ["obs:csq:public-approach"], []))

    # South / High Street: conservative public-facing rhythm with landscape-obscured ground interface.
    south_v = v_min - 0.10
    meshes.append(_oriented_box(scene_tools, "CSQ_FACADE_HIGH_STREET_Ground_Storefront", _point(origin, 0, south_v), (u_span * 0.82, 0.24, 4.15), 2.4, mats["storefront"], groups["FACADE_HIGH_STREET"], "csq:facade:south-ground-retail", "VERIFIED_PHOTOGRAPHIC", ["obs:csq:south-facade"], ["ref:commons:158404929", "ref:commons:158404930"]))
    meshes.append(_oriented_box(scene_tools, "CSQ_FACADE_HIGH_STREET_Tall_Glazed_Strip", _point(origin, 19.0, south_v - 0.02), (10.0, 0.28, 17.5), 14.65, mats["dark_glass"], groups["FACADE_HIGH_STREET"], "csq:facade:south-tall-glazed-strip", "VERIFIED_PHOTOGRAPHIC", ["obs:csq:south-facade"], ["ref:commons:158404929"]))
    for index, u_pos in enumerate((-29.0, -15.0, 0.0, 15.0, 29.0), start=1):
        meshes.append(_oriented_box(scene_tools, f"CSQ_STRUCTURE_High_Street_Column_{index:02d}", _point(origin, u_pos, south_v - 0.35), (0.65, 0.65, 5.0), 2.5, mats["metal"], groups["STRUCTURAL_ELEMENTS"], f"csq:structure:south-column-{index:02d}", "PROCEDURAL", ["obs:csq:south-facade"], ["ref:commons:158404929"]))

    # East/service side intentionally receives no invented openings.
    east_u = u_max + 0.06
    meshes.append(_oriented_box(scene_tools, "CSQ_FACADE_OTHER_Neutral_Plane", _point(origin, east_u, 0), (0.18, v_span * 0.80, 20.0), 14.0, mats["warm"], groups["FACADE_OTHER"], "csq:facade:east-procedural", "PROCEDURAL", ["obs:csq:dominant-massing"], []))

    roof = scene_tools.create_extruded_polygons(
        "CSQ_ROOF_Major_Plane",
        [main_feature["geometry"]["coordinates"]],
        25.55,
        0.35,
        mats["roof"],
        "verified broad flat roof; procedural finish; equipment omitted",
    )
    roof.parent = groups["ROOF"]
    meshes.append(_tag(roof, "csq:massing:roof-plane", "VERIFIED_PHOTOGRAPHIC", ["obs:csq:roof"], ["ref:commons:173664145", "ref:commons:173664147"]))

    for obj in meshes:
        obj["geographic_anchor_preserved"] = True
    root["mesh_count"] = len(meshes)
    root["unknowns_omitted"] = "east openings; exact south portal; basement ramp; roof mechanical equipment; exact mullion spacing"
    return meshes


def select_exportables(objects: Iterable[bpy.types.Object]) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        if obj.type == "MESH" and obj.get("exportable"):
            obj.select_set(True)
