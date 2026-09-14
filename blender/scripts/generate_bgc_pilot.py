"""Generate the geographically grounded low-fidelity BGC pilot scene."""

from __future__ import annotations

import json
import importlib.util
import math
from pathlib import Path
import re
import sys
import traceback


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import bpy

from scene_tools import (
    add_camera,
    add_daylight,
    clear_scene,
    configure_scene,
    create_box_cluster,
    create_extruded_polygons,
    create_material,
    create_tree_cluster,
    export_glb,
    geojson_polygons,
    render_png,
    save_blend,
)


ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
ASSET_REGISTRY = ROOT / "data" / "assets" / "buildings.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from blender.framework.export import merge_runtime_in_place


def load_reconstructed_assets() -> list[tuple[dict, object | None]]:
    registry = json.loads(ASSET_REGISTRY.read_text(encoding="utf-8"))
    loaded = []
    for entry in registry.get("buildings", {}).values():
        lod = entry.get("available_lods", {}).get("1")
        if not lod or lod.get("status") != "APPROVED":
            continue
        module = None
        if entry.get("builder_module"):
            module_path = ROOT / entry["builder_module"]
            spec = importlib.util.spec_from_file_location(f"bgc_builder_{entry['entity_id']}", module_path)
            if spec is None or spec.loader is None:
                raise RuntimeError(f"Cannot load registered builder: {module_path}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        loaded.append((entry, module))
    return loaded


def load(name: str) -> dict:
    return json.loads((PROCESSED / name).read_text(encoding="utf-8"))


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_")[:55] or "unnamed"


def polygon_list(features: list[dict]) -> list[list[list[float]]]:
    polygons = []
    for feature in features:
        polygons.extend(geojson_polygons(feature["geometry"]))
    return polygons


def geometry_points(geometry: dict):
    coordinates = geometry["coordinates"]
    if geometry["type"] == "Point":
        yield coordinates
    elif geometry["type"] == "Polygon":
        for ring in coordinates:
            yield from ring
    elif geometry["type"] == "MultiPolygon":
        for polygon in coordinates:
            for ring in polygon:
                yield from ring


def main() -> None:
    buildings_payload = load("pilot-buildings.geojson")
    roads_payload = load("pilot-roads.geojson")
    paths_payload = load("pilot-paths.geojson")
    spaces_payload = load("pilot-open-spaces.geojson")
    road_surfaces_payload = load("pilot-road-surfaces.geojson")
    path_surfaces_payload = load("pilot-path-surfaces.geojson")
    open_space_surfaces_payload = load("pilot-open-space-surfaces.geojson")
    pois_payload = load("pilot-pois.geojson")
    boundary_payload = load("pilot-boundary-local.geojson")
    datasets = [buildings_payload, roads_payload, paths_payload, spaces_payload, pois_payload, road_surfaces_payload, path_surfaces_payload, open_space_surfaces_payload]
    source_hashes = {payload["source_sha256"] for payload in datasets}
    if len(source_hashes) != 1:
        raise RuntimeError(f"Processed datasets do not share one source snapshot: {source_hashes}")

    clear_scene()
    configure_scene()
    scene = bpy.context.scene
    scene["dataset_id"] = "bgc-pilot-base-v1"
    scene["source_id"] = "source:osm"
    scene["source_sha256"] = next(iter(source_hashes))
    scene["source_retrieved_at"] = buildings_payload["source_retrieved_at"]
    scene["horizontal_crs"] = "EPSG:32651"
    scene["local_origin_wgs84"] = "121.050972,14.550806"
    scene["units"] = "metres"

    materials = {
        "ground": create_material("BGC_Ground_Procedural", (0.075, 0.085, 0.08, 1.0)),
        "road": create_material("BGC_Road_EstimatedWidth", (0.075, 0.09, 0.105, 1.0), roughness=0.92),
        "path": create_material("BGC_Path_EstimatedWidth", (0.48, 0.47, 0.40, 1.0), roughness=0.88),
        "open": create_material("BGC_OpenSpace_Verified", (0.13, 0.30, 0.16, 1.0), roughness=0.9),
        "VERIFIED_GEOGRAPHIC": create_material("BGC_Height_VerifiedGeographic", (0.12, 0.39, 0.62, 1.0)),
        "ESTIMATED": create_material("BGC_Height_Estimated", (0.82, 0.48, 0.10, 1.0)),
        "PROCEDURAL": create_material("BGC_Height_Procedural", (0.62, 0.19, 0.34, 1.0)),
        "trunk": create_material("BGC_Tree_Trunk_Procedural", (0.22, 0.12, 0.06, 1.0)),
        "crown": create_material("BGC_Tree_Crown_Procedural", (0.08, 0.32, 0.11, 1.0)),
        "furniture": create_material("BGC_Furniture_Procedural", (0.22, 0.24, 0.25, 1.0), metallic=0.15),
    }

    boundary_feature = boundary_payload["features"][0]
    ground = create_extruded_polygons(
        "BGC_Pilot_Ground",
        geojson_polygons(boundary_feature["geometry"]),
        -0.18,
        0.18,
        materials["ground"],
        "procedurally generated filler over estimated pilot boundary",
    )
    ground["source_scope"] = boundary_feature["properties"]["name"]

    if roads_payload["features"]:
        road = create_extruded_polygons("BGC_Road_Network", polygon_list(road_surfaces_payload["features"]), 0.0, 0.07, materials["road"], "estimated surface from verified geographic centerlines")
        road["source_feature_count"] = len(roads_payload["features"])
    if spaces_payload["features"]:
        spaces = create_extruded_polygons("BGC_Open_Spaces", polygon_list(open_space_surfaces_payload["features"]), 0.075, 0.045, materials["open"], "verified geographic area with procedural material")
        spaces["source_feature_count"] = len(spaces_payload["features"])
    if paths_payload["features"]:
        paths = create_extruded_polygons("BGC_Pedestrian_Network", polygon_list(path_surfaces_payload["features"]), 0.125, 0.045, materials["path"], "estimated surface from verified geographic path geometry")
        paths["source_feature_count"] = len(paths_payload["features"])

    use_reconstructed_assets = "--base-lod-only" not in sys.argv and "--central-square-lod2" not in sys.argv
    reconstructed_assets = load_reconstructed_assets() if use_reconstructed_assets else []
    replaced_source_ids = {
        source_id for entry, _module in reconstructed_assets
        for source_id in entry.get("source_feature_ids", [])
    }
    building_count = 0
    for feature in buildings_payload["features"]:
        properties = feature["properties"]
        if properties["id"] in replaced_source_ids:
            continue
        top = float(properties["height_m"])
        base = float(properties.get("min_height_m", 0.0))
        thickness = max(0.25, top - base)
        status = properties["height_status"]
        label = safe_name(properties.get("name") or properties["id"])
        obj = create_extruded_polygons(
            f"BGC_Building_{label}_{building_count:03d}",
            geojson_polygons(feature["geometry"]),
            base,
            thickness,
            materials[status],
            f"verified geographic footprint; {status.lower()} height",
        )
        obj["entity_id"] = properties["id"]
        obj["feature_kind"] = properties["feature_kind"]
        obj["height_status"] = status
        obj["height_method"] = properties["height_method"]
        obj["height_m"] = top
        obj["source_id"] = "source:osm"
        building_count += 1

    if reconstructed_assets:
        reconstructed_mesh_count = 0
        for entry, module in reconstructed_assets:
            if module is None:
                before = set(bpy.context.scene.objects)
                asset_path = ROOT / entry["available_lods"]["1"]["asset"]
                bpy.ops.import_scene.gltf(filepath=str(asset_path))
                meshes = [obj for obj in bpy.context.scene.objects if obj not in before and obj.type == "MESH"]
            else:
                meshes = module.build(scene_tools=sys.modules["scene_tools"])
            if module is not None and entry.get("runtime_merge_groups"):
                meshes = merge_runtime_in_place(meshes, entry["runtime_merge_groups"])
            reconstructed_mesh_count += len(meshes)
            building_count += 1
        scene["reconstructed_asset_lod"] = "LOD1"
        scene["reconstructed_asset_count"] = len(reconstructed_assets)
        scene["reconstructed_asset_mesh_count"] = reconstructed_mesh_count
    else:
        scene["reconstructed_asset_lod"] = "LOD2_BASE"
        scene["reconstructed_asset_count"] = 0

    node_pois = [feature for feature in pois_payload["features"] if feature["properties"]["id"].startswith("osm:node:")]
    tree_points = [tuple(feature["geometry"]["coordinates"]) for feature in node_pois if feature["properties"].get("category") == "tree"]
    furniture_categories = {"bench", "waste_basket", "bicycle_parking", "street_lamp"}
    furniture_points = [tuple(feature["geometry"]["coordinates"]) for feature in node_pois if feature["properties"].get("category") in furniture_categories]
    tree_objects = create_tree_cluster("BGC_OSM_Trees", tree_points, materials["trunk"], materials["crown"])
    for obj in tree_objects:
        obj["source_feature_count"] = len(tree_points)
    furniture = create_box_cluster("BGC_OSM_Street_Furniture", furniture_points, (0.45, 0.45, 1.1), 0.13, materials["furniture"])
    if furniture:
        furniture["source_feature_count"] = len(furniture_points)

    all_points = list(geometry_points(boundary_feature["geometry"]))
    min_x, max_x = min(point[0] for point in all_points), max(point[0] for point in all_points)
    min_y, max_y = min(point[1] for point in all_points), max(point[1] for point in all_points)
    center_x, center_y = (min_x + max_x) / 2.0, (min_y + max_y) / 2.0
    extent = max(max_x - min_x, max_y - min_y)
    max_height = max(float(feature["properties"]["height_m"]) for feature in buildings_payload["features"])

    add_daylight()
    cameras = [
        ("Pilot_Aerial", (center_x + extent * 0.55, center_y - extent * 0.60, extent * 0.82), (center_x, center_y, max_height * 0.12), 52.0, "aerial.png"),
        ("Pilot_North_Oblique", (center_x - extent * 0.18, max_y + extent * 0.62, extent * 0.44), (center_x, center_y, max_height * 0.16), 55.0, "north-oblique.png"),
        ("Pilot_South_Oblique", (center_x + extent * 0.18, min_y - extent * 0.62, extent * 0.44), (center_x, center_y, max_height * 0.16), 55.0, "south-oblique.png"),
        ("Pilot_Street_01", (-175.0, 50.0, 5.2), (-300.0, 50.0, 7.0), 44.0, "street-test-01.png"),
        ("Pilot_Street_02", (45.0, -55.0, 5.2), (58.0, 68.0, 9.0), 44.0, "street-test-02.png"),
    ]
    render_dir = ROOT / "blender" / "renders" / "pilot"
    for name, location, target, lens, filename in cameras:
        add_camera(name, location, target, lens=lens)
        render_png(render_dir / filename)

    scene["building_count"] = building_count
    scene["road_count"] = len(roads_payload["features"])
    scene["path_count"] = len(paths_payload["features"])
    scene["open_space_count"] = len(spaces_payload["features"])
    scene["tree_count"] = len(tree_points)
    scene["street_furniture_count"] = len(furniture_points)
    save_blend(ROOT / "blender" / "scenes" / "bgc-pilot-base.blend")
    export_glb(ROOT / "exports" / "glb" / "bgc-pilot-base.glb")
    print(
        "BGC_PILOT: generated "
        f"buildings={building_count} roads={len(roads_payload['features'])} "
        f"paths={len(paths_payload['features'])} trees={len(tree_points)} furniture={len(furniture_points)}"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
