"""Evidence-aware LOD1 interpretation of W Global Center."""

from __future__ import annotations

import json
import math
from pathlib import Path
import sys
from typing import Iterable

import bpy


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = ROOT / "data" / "reconstruction_packages" / "bgc_building_0007"
for path in (ROOT, ROOT / "blender" / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from blender.framework.geometry import FacadeFrame, OpenFacadeBand, WindowGrid
from blender.framework.materials import create_material_family
from blender.framework.metadata import apply_component_metadata


ENTITY_ID = "bgc_building_0007"
HEIGHT_M = 30.5


def _load(name: str) -> dict:
    return json.loads((PACKAGE / name).read_text(encoding="utf-8"))


def _tag(obj, component_id: str, status: str, observations: Iterable[str], evidence: Iterable[str] = ()):
    apply_component_metadata(
        obj, entity_id=ENTITY_ID, component_id=component_id,
        component_type=component_id.split(":", 2)[1], evidence_status=status,
        observation_ids=observations, evidence_ids=evidence,
        reconstruction_fidelity="LOD1_MEDIUM_ARCHITECTURAL_FIDELITY",
        target_time_state="CURRENT_APPROX_2025_2026",
    )
    obj["lod"] = "LOD1"
    return obj


def _empty(name: str, parent=None):
    obj = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = parent
    return obj


def _facade_box(scene_tools, frame: FacadeFrame, name: str, component_id: str,
                u0: float, u1: float, v0: float, v1: float, depth_m: float,
                thickness_m: float, material, parent, status: str,
                observations: Iterable[str], evidence: Iterable[str] = ()):
    placement = frame.region(u0, u1, v0, v1, depth_m)
    obj = scene_tools.create_box(
        name, (*placement["center_xy"], placement["center_z"]),
        (placement["width_m"], thickness_m, placement["height_m"]), material,
    )
    obj.rotation_euler[2] = math.radians(frame.angle_deg)
    obj.parent = parent
    return _tag(obj, component_id, status, observations, evidence)


def _diagonal(scene_tools, frame: FacadeFrame, name: str, component_id: str,
              u0: float, u1: float, z0: float, z1: float, material, parent):
    p0, p1 = frame.point(u0, 0.32), frame.point(u1, 0.32)
    horizontal = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    length = math.hypot(horizontal, z1 - z0)
    obj = scene_tools.create_box(name, ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, (z0 + z1) / 2), (length, 0.28, 0.28), material)
    obj.rotation_euler[2] = math.radians(frame.angle_deg)
    obj.rotation_euler[1] = -math.atan2(z1 - z0, horizontal)
    obj.parent = parent
    return _tag(obj, component_id, "VERIFIED_PHOTOGRAPHIC", ["obs:wgc:facades", "obs:wgc:floor-organization"], ["ref:web:officepro-w-global"])


def build(scene_tools, parent=None) -> list:
    geometry = _load("geometry.geojson")
    feature = geometry["features"][0]
    ring = feature["geometry"]["coordinates"][0]
    # Street-grounded edges: B->C faces 30th Street; C->D faces 9th Avenue.
    b, c, d = tuple(ring[1]), tuple(ring[2]), tuple(ring[3])
    frame_30th = FacadeFrame(b, math.dist(b, c), HEIGHT_M, math.degrees(math.atan2(c[1] - b[1], c[0] - b[0])), -1.0)
    frame_9th = FacadeFrame(c, math.dist(c, d), HEIGHT_M, math.degrees(math.atan2(d[1] - c[1], d[0] - c[0])), -1.0)

    root = _empty("WGC_ROOT", parent)
    root["entity_id"] = ENTITY_ID
    root["source_package"] = "data/reconstruction_packages/bgc_building_0007"
    root["height_m"] = HEIGHT_M
    root["height_status"] = "VERIFIED_GEOGRAPHIC_NOT_SURVEYED"
    root["physical_storey_count"] = "CONFLICTED_7_VS_8"
    root["coordinate_frame"] = "BGC local metres: X east, Y north, Z up"
    groups = {name: _empty(f"WGC_{name}", root) for name in (
        "MASSING", "FACADE_30TH", "FACADE_9TH", "FACADE_WEAK",
        "OPEN_BANDS", "WINDOWS", "STRUCTURE", "ENTRANCE", "ROOF",
    )}
    mats = {
        "light": create_material_family(scene_tools, "light_neutral_panel"),
        "glass": create_material_family(scene_tools, "architectural_dark_glass"),
        "storefront": create_material_family(scene_tools, "generic_storefront_glass"),
        "metal": create_material_family(scene_tools, "dark_metal"),
        "concrete": create_material_family(scene_tools, "neutral_roof"),
    }
    meshes = []
    shell = scene_tools.create_extruded_polygons(
        "WGC_MASSING_Envelope", [feature["geometry"]["coordinates"]], 0.0, 27.5,
        mats["light"], "mapped footprint; main roof estimated below the 30.5 m frame-inclusive maximum",
    )
    shell.parent = groups["MASSING"]
    meshes.append(_tag(shell, "wgc:massing:envelope", "VERIFIED_GEOGRAPHIC", ["obs:wgc:footprint", "obs:wgc:height", "obs:wgc:massing"], ["source:osm", "ref:web:officepro-w-global"]))

    for label, frame, group in (("30TH", frame_30th, groups["FACADE_30TH"]), ("9TH", frame_9th, groups["FACADE_9TH"])):
        meshes.append(_facade_box(scene_tools, frame, f"WGC_{label}_Ground_Glazing", f"wgc:facade:{label.lower()}-ground-glazing", 0.03, 0.97, 0.02, 0.18, 0.24, 0.22, mats["storefront"], group, "VERIFIED_PHOTOGRAPHIC", ["obs:wgc:facades", "obs:wgc:entrance"], ["ref:web:officepro-w-global"]))
        for band_index, band in enumerate((OpenFacadeBand(5.5, 4.0), OpenFacadeBand(9.5, 4.0)), start=1):
            parts = band.parts()
            for part_name in ("bottom_slab", "guard_band", "top_slab"):
                base, height = parts[part_name]
                material = mats["metal"] if part_name == "guard_band" else mats["concrete"]
                meshes.append(_facade_box(scene_tools, frame, f"WGC_{label}_OpenBand_{band_index}_{part_name}", f"wgc:open-band:{label.lower()}-{band_index}-{part_name}", 0.01, 0.99, base / HEIGHT_M, (base + height) / HEIGHT_M, 0.30, 0.26, material, groups["OPEN_BANDS"], "VERIFIED_PHOTOGRAPHIC", ["obs:wgc:floor-organization", "obs:wgc:facades"], ["ref:web:officepro-w-global", "ref:web:kmc-w-global-brochure"]))
            meshes.append(_facade_box(scene_tools, frame, f"WGC_{label}_OpenBand_{band_index}_Shadow", f"wgc:open-band:{label.lower()}-{band_index}-shadow", 0.02, 0.98, (band.base_z_m + 0.38) / HEIGHT_M, (band.base_z_m + band.height_m - 0.38) / HEIGHT_M, -0.02, 0.12, mats["glass"], groups["OPEN_BANDS"], "VERIFIED_PHOTOGRAPHIC", ["obs:wgc:floor-organization"], ["ref:web:officepro-w-global"]))
        brace_count = 2 if label == "30TH" else 3
        for index in range(brace_count):
            u0 = 0.08 + index * (0.82 / brace_count)
            u1 = u0 + 0.18
            meshes.append(_diagonal(scene_tools, frame, f"WGC_{label}_Brace_{index + 1:02d}", f"wgc:structure:{label.lower()}-brace-{index + 1:02d}", u0, u1, 6.1, 12.9, mats["metal"], groups["STRUCTURE"]))

    grids = (
        ("30th", frame_30th, WindowGrid(6, 4, 0.05, 0.72, 0.48, 0.90)),
        ("9th", frame_9th, WindowGrid(8, 4, 0.28, 0.96, 0.48, 0.90)),
    )
    for side, frame, grid in grids:
        for index, (u0, u1, v0, v1) in enumerate(grid.regions(), start=1):
            meshes.append(_facade_box(scene_tools, frame, f"WGC_WINDOW_{side.upper()}_{index:02d}", f"wgc:window:{side}-{index:02d}", u0, u1, v0, v1, 0.31, 0.16, mats["glass"], groups["WINDOWS"], "INFERRED", ["obs:wgc:facades"], ["ref:web:officepro-w-global"]))

    meshes.append(_facade_box(scene_tools, frame_30th, "WGC_30TH_Corner_Glass", "wgc:facade:30th-corner-glass", 0.76, 0.98, 0.46, 0.91, 0.33, 0.18, mats["glass"], groups["FACADE_30TH"], "VERIFIED_PHOTOGRAPHIC", ["obs:wgc:facades"], ["ref:web:officepro-w-global"]))
    meshes.append(_facade_box(scene_tools, frame_9th, "WGC_9TH_Corner_Glass", "wgc:facade:9th-corner-glass", 0.02, 0.23, 0.46, 0.91, 0.33, 0.18, mats["glass"], groups["FACADE_9TH"], "VERIFIED_PHOTOGRAPHIC", ["obs:wgc:facades"], ["ref:web:officepro-w-global"]))
    meshes.append(_facade_box(scene_tools, frame_30th, "WGC_Entrance_Corner", "wgc:entrance:corner-public", 0.73, 0.96, 0.01, 0.15, 0.36, 0.20, mats["glass"], groups["ENTRANCE"], "INFERRED", ["obs:wgc:entrance"], ["ref:web:officepro-w-global"]))

    # The distinctive frame is configured from observed silhouette; it is not a structural claim.
    for index, (u0, u1, v0, v1) in enumerate(((0.76, 0.79, 0.88, 1.0), (0.96, 0.99, 0.88, 1.0), (0.76, 0.99, 0.97, 1.0)), start=1):
        meshes.append(_facade_box(scene_tools, frame_30th, f"WGC_ROOF_Frame_{index:02d}", f"wgc:roof:corner-frame-{index:02d}", u0, u1, v0, v1, 0.25, 0.55, mats["light"], groups["ROOF"], "VERIFIED_PHOTOGRAPHIC", ["obs:wgc:roof"], ["ref:web:officepro-w-global", "ref:web:colliers-w-global"]))

    root["mesh_count"] = len(meshes)
    root["unknowns_omitted"] = "exact storey count; opposite-side openings; exact portal; roof plant; exact mullion spacing"
    return meshes
