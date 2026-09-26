"""Generate deterministic web-oriented M11 tile scenes and GLBs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import traceback

import bpy

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from scene_tools import clear_scene, configure_scene, create_extruded_polygons, create_material, export_glb, geojson_polygons, save_blend


ROOT = Path(__file__).resolve().parents[2]
INPUT_DIR = ROOT / "data" / "processed" / "bgc-tiles"
OUTPUT_DIR = ROOT / "exports" / "bgc" / "tiles"
SCENE_DIR = ROOT / "blender" / "scenes" / "bgc" / "tiles"
MANIFEST_PATH = ROOT / "exports" / "bgc" / "manifest.json"
METRICS_DIR = ROOT / "data" / "reports" / "bgc-tiles"


def polygons(geometry: dict) -> list[list[list[float]]]:
    if geometry.get("type") in {"Polygon", "MultiPolygon"}:
        return geojson_polygons(geometry)
    if geometry.get("type") == "GeometryCollection":
        result = []
        for child in geometry.get("geometries", []):
            result.extend(polygons(child))
        return result
    return []


def building_palette(properties: dict) -> str:
    building_type = str(properties.get("tags", {}).get("building", "")).lower()
    if building_type in {"apartments", "residential", "house", "dormitory"}:
        return "residential"
    if building_type in {"retail", "commercial", "kiosk"}:
        return "retail"
    if building_type in {"office", "civic", "government"}:
        return "office"
    return "neutral"


def merge_objects(objects: list[bpy.types.Object], name: str, entity_ids: list[str]) -> bpy.types.Object | None:
    if not objects:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    merged = bpy.context.object
    merged.name = name
    merged["entity_ids"] = json.dumps(sorted(set(entity_ids)), separators=(",", ":"))
    merged["entity_lookup"] = "exports/bgc/manifest.json"
    return merged


def geometry_metrics() -> dict:
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    return {
        "mesh_count": len(meshes),
        "triangle_count": sum(sum(max(0, len(polygon.vertices) - 2) for polygon in obj.data.polygons) for obj in meshes),
        "material_count": len({material.name for obj in meshes for material in obj.data.materials if material}),
    }


def build_tile(input_path: Path, debug_heights: bool, representation: str = "merged", output_suffix: str = "") -> dict:
    tile = json.loads(input_path.read_text(encoding="utf-8"))
    tile_id = tile["tile_id"]
    clear_scene()
    configure_scene()
    scene = bpy.context.scene
    scene["dataset_id"] = "bgc-whole-city-lod2-v1"
    scene["tile_id"] = tile_id
    scene["pipeline_version"] = tile["pipeline_version"]
    scene["input_sha256"] = tile["input_sha256"]
    scene["source_sha256"] = tile["source_sha256"]
    scene["horizontal_crs"] = "EPSG:32651"
    scene["local_origin_wgs84"] = "121.050972,14.550806"
    scene["units"] = "metres"
    scene["lod"] = "LOD2"

    materials = {
        "ground": create_material("BGC_Ground", (0.10, 0.115, 0.105, 1)),
        "road": create_material("BGC_Road", (0.055, 0.065, 0.075, 1), roughness=0.94),
        "path": create_material("BGC_Path", (0.48, 0.45, 0.38, 1), roughness=0.9),
        "open": create_material("BGC_OpenSpace", (0.12, 0.29, 0.14, 1), roughness=0.92),
        "neutral": create_material("BGC_Generic_Neutral", (0.46, 0.50, 0.52, 1)),
        "residential": create_material("BGC_Generic_Residential", (0.52, 0.45, 0.40, 1)),
        "retail": create_material("BGC_Generic_Retail", (0.56, 0.48, 0.34, 1)),
        "office": create_material("BGC_Generic_Office", (0.29, 0.42, 0.48, 1), roughness=0.48, metallic=0.05),
        "VERIFIED_GEOGRAPHIC": create_material("BGC_Debug_Height_Verified", (0.10, 0.42, 0.72, 1)),
        "ESTIMATED": create_material("BGC_Debug_Height_Estimated", (0.90, 0.52, 0.08, 1)),
        "PROCEDURAL": create_material("BGC_Debug_Height_Procedural", (0.70, 0.14, 0.28, 1)),
    }

    heights = json.loads((ROOT / "data/config/surface-heights.json").read_text())
    ground_polygons = polygons(tile["ground"])
    if ground_polygons:
        create_extruded_polygons(f"{tile_id}_ground", ground_polygons, heights["GROUND_TOP"] - 0.16, 0.16, materials["ground"], "procedurally generated ground clipped to estimated working boundary")
    context_specs = tuple((source, material, heights[key + "_TOP"] - heights[key + "_THICKNESS"], heights[key + "_THICKNESS"]) for source, material, key in (("roads", "road", "ROAD"), ("open_spaces", "open", "OPEN_SPACE"), ("paths", "path", "PATH")))
    for key, material_key, base, height in context_specs:
        context_polygons = [polygon for feature in tile[key] for polygon in polygons(feature["geometry"])]
        if context_polygons:
            create_extruded_polygons(f"{tile_id}_{key}", context_polygons, base, height, materials[material_key], "verified geographic geometry with simple M11 material")

    grouped: dict[str, list[bpy.types.Object]] = {}
    entity_ids: dict[str, list[str]] = {}
    entity_records = []
    for index, feature in enumerate(tile["buildings"]):
        props = feature["properties"]
        base = float(props.get("min_height_m", 0.0))
        top = float(props["height_m"])
        if top <= base:
            continue
        key = props["height_status"] if debug_heights else (f"detailed_{props['detailed_asset_id']}" if props.get("detailed_asset_id") else building_palette(props))
        material_key = props["height_status"] if debug_heights else building_palette(props)
        obj = create_extruded_polygons(
            f"{tile_id}_building_{index:04d}", polygons(feature["geometry"]), base, top - base,
            materials[material_key], f"verified geographic footprint; {props['height_status'].lower()} height; LOD2",
        )
        obj["entity_id"] = props["canonical_entity_id"]
        obj["source_feature_id"] = props["id"]
        obj["height_m"] = top
        obj["height_status"] = props["height_status"]
        obj["lod"] = "LOD2"
        grouped.setdefault(key, []).append(obj)
        entity_ids.setdefault(key, []).append(props["canonical_entity_id"])
        entity_records.append({
            "entity_id": props["canonical_entity_id"], "source_feature_id": props["id"], "name": props.get("name"),
            "height_m": top, "height_status": props["height_status"], "building_type": props.get("tags", {}).get("building"),
            "lod": "LOD2", "render_role": props["render_role"],
        })
    if representation == "merged":
        for key in sorted(grouped):
            merged = merge_objects(grouped[key], f"{tile_id}_buildings_{key}", entity_ids[key])
            if merged is not None and key.startswith("detailed_"):
                merged["detailed_asset_id"] = key.removeprefix("detailed_")

    metrics = geometry_metrics()
    scene["building_entity_count"] = len(set(record["entity_id"] for record in entity_records))
    scene["building_volume_count"] = len(entity_records)
    scene["runtime_representation"] = "MERGED_BY_TILE_MATERIAL" if representation == "merged" else "PER_BUILDING"
    scene["debug_height_materials"] = debug_heights
    SCENE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    save_blend(SCENE_DIR / f"{tile_id}{output_suffix}.blend")
    output = OUTPUT_DIR / f"{tile_id}{output_suffix}.glb"
    export_glb(output)
    output_hash = hashlib.sha256(output.read_bytes()).hexdigest()
    result = {
        "status": "PASS", "tile_id": tile_id, "input_sha256": tile["input_sha256"], "output_sha256": output_hash,
        "building_count": scene["building_entity_count"], "render_volume_count": len(entity_records), **metrics,
        "bytes": output.stat().st_size, "entities": entity_records,
    }
    result["representation"] = scene["runtime_representation"]
    (METRICS_DIR / f"{tile_id}{output_suffix}.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"BGC_TILE PASS {tile_id} buildings={result['building_count']} triangles={result['triangle_count']} meshes={result['mesh_count']} materials={result['material_count']} bytes={result['bytes']}")
    return result


def update_manifest(results: dict[str, dict]) -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    for tile in manifest["tiles"]:
        result = results.get(tile["tile_id"])
        if not result:
            continue
        for key in ("status", "triangle_count", "mesh_count", "material_count", "bytes", "output_sha256"):
            tile[key] = result[key]
    completed = [tile for tile in manifest["tiles"] if tile["status"] == "PASS"]
    manifest["totals"].update({
        "completed_tiles": len(completed), "glb_bytes": sum(tile["bytes"] for tile in completed),
        "triangles": sum(tile["triangle_count"] for tile in completed), "runtime_nodes": sum(tile["mesh_count"] for tile in completed),
    })
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--tile")
    parser.add_argument("--debug-heights", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--representation", choices=("merged", "per-building"), default="merged")
    args = parser.parse_args(argv)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    selected = [tile for tile in manifest["tiles"] if not args.tile or tile["tile_id"] == args.tile]
    if args.tile and not selected:
        raise ValueError(f"Unknown tile: {args.tile}")
    if args.representation == "per-building" and len(selected) != 1:
        raise ValueError("--representation per-building requires exactly one --tile")
    results = {}
    failures = []
    for tile in selected:
        metrics_path = METRICS_DIR / f"{tile['tile_id']}.json"
        output_path = OUTPUT_DIR / f"{tile['tile_id']}.glb"
        if args.representation == "merged" and not args.force and not args.debug_heights and metrics_path.is_file() and output_path.is_file():
            cached = json.loads(metrics_path.read_text(encoding="utf-8"))
            if cached.get("input_sha256") == tile["input_sha256"]:
                results[tile["tile_id"]] = cached
                print(f"BGC_TILE CACHED {tile['tile_id']}")
                continue
        try:
            suffix = "_per-building" if args.representation == "per-building" else ""
            results[tile["tile_id"]] = build_tile(ROOT / tile["input_path"], args.debug_heights, args.representation, suffix)
        except Exception as error:
            traceback.print_exc()
            failures.append({"tile_id": tile["tile_id"], "status": "FAIL", "error": str(error)})
            print(f"BGC_TILE FAIL {tile['tile_id']} error={error}")
    if args.representation == "merged":
        update_manifest(results)
    if failures:
        (ROOT / "data" / "reports" / "bgc-tile-failures.json").write_text(json.dumps(failures, indent=2) + "\n", encoding="utf-8")
        raise RuntimeError(f"{len(failures)} tile(s) failed")


if __name__ == "__main__":
    main()
