"""Build deterministic, part-aware M11 tile inputs and a sidecar manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from shapely import make_valid
from shapely.geometry import box, mapping, shape
from shapely.ops import unary_union


ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
TILE_INPUTS = PROCESSED / "bgc-tiles"
MANIFEST_PATH = ROOT / "exports" / "bgc" / "manifest.json"
PIPELINE_VERSION = 1


def read(name: str) -> dict[str, Any]:
    return json.loads((PROCESSED / name).read_text(encoding="utf-8"))


def stable_json(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def clean_mapping(geometry) -> dict[str, Any]:
    value = mapping(make_valid(geometry))
    return json.loads(json.dumps(value, allow_nan=False))


def feature_copy(feature: dict[str, Any], geometry=None, **properties: Any) -> dict[str, Any]:
    result = {
        "type": "Feature",
        "id": feature["properties"]["id"],
        "properties": {**feature["properties"], **properties},
        "geometry": clean_mapping(geometry if geometry is not None else shape(feature["geometry"])),
    }
    return result


def tile_id(column: int, row: int) -> str:
    return f"tile_{column:03d}_{row:03d}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tile-size", type=float, default=250.0)
    args = parser.parse_args()
    if args.tile_size <= 0:
        raise ValueError("--tile-size must be positive")

    datasets = {
        "buildings": read("bgc-buildings.geojson"),
        "roads": read("bgc-roads.geojson"),
        "paths": read("bgc-paths.geojson"),
        "open_spaces": read("bgc-open-spaces.geojson"),
        "boundary": read("bgc-boundary-local.geojson"),
    }
    source_hashes = {payload.get("source_sha256") for key, payload in datasets.items() if key != "boundary"}
    if len(source_hashes) != 1:
        raise RuntimeError(f"Whole-city datasets do not share one source snapshot: {source_hashes}")
    source_hash = next(iter(source_hashes))
    boundary = shape(datasets["boundary"]["features"][0]["geometry"])
    min_x, min_y, max_x, max_y = boundary.bounds
    origin_x = math.floor(min_x / args.tile_size) * args.tile_size
    origin_y = math.floor(min_y / args.tile_size) * args.tile_size

    raw_buildings = datasets["buildings"]["features"]
    outlines = [feature for feature in raw_buildings if feature["properties"]["feature_kind"] == "building_outline"]
    parts = [feature for feature in raw_buildings if feature["properties"]["feature_kind"] == "building_part"]
    outline_geometries = {feature["properties"]["id"]: shape(feature["geometry"]) for feature in outlines}
    part_parent: dict[str, str] = {}
    anomalies: list[dict[str, Any]] = []
    for part in parts:
        part_id = part["properties"]["id"]
        geometry = shape(part["geometry"])
        candidates = [
            (outline_geometries[outline["properties"]["id"]].area, outline["properties"]["id"])
            for outline in outlines
            if outline_geometries[outline["properties"]["id"]].covers(geometry.representative_point())
        ]
        if candidates:
            part_parent[part_id] = min(candidates)[1]
        else:
            anomalies.append({"entity_id": part_id, "category": "SOURCE_DATA_ISSUE", "issue": "orphan_part"})

    parts_by_parent: dict[str, list[dict[str, Any]]] = {}
    for part in parts:
        parent = part_parent.get(part["properties"]["id"])
        if parent:
            parts_by_parent.setdefault(parent, []).append(part)

    renderables: list[dict[str, Any]] = []
    canonical_owner_geometry: dict[str, Any] = {}
    for outline in outlines:
        props = outline["properties"]
        entity_id = props["id"]
        geometry = outline_geometries[entity_id]
        canonical_owner_geometry[entity_id] = geometry
        related = parts_by_parent.get(entity_id, [])
        if related:
            part_union = unary_union([shape(part["geometry"]) for part in related])
            residual = make_valid(geometry.difference(part_union))
            if not residual.is_empty and residual.area >= 0.5:
                renderables.append(feature_copy(outline, residual, render_role="outline_residual", canonical_entity_id=entity_id))
            for part in related:
                part_props = part["properties"]
                renderables.append(feature_copy(part, canonical_entity_id=entity_id, render_role="building_part", parent_outline_id=entity_id))
                if float(part_props["height_m"]) > max(float(props["height_m"]) * 1.5, float(props["height_m"]) + 40):
                    anomalies.append({"entity_id": part_props["id"], "category": "SOURCE_DATA_ISSUE", "issue": "part_height_parent_mismatch", "parent_id": entity_id})
        else:
            renderables.append(feature_copy(outline, canonical_entity_id=entity_id, render_role="building_outline"))

    for part in parts:
        entity_id = part["properties"]["id"]
        if entity_id not in part_parent:
            canonical_owner_geometry[entity_id] = shape(part["geometry"])
            renderables.append(feature_copy(part, canonical_entity_id=entity_id, render_role="orphan_part"))

    registry = json.loads((ROOT / "data" / "assets" / "buildings.json").read_text(encoding="utf-8"))
    detailed_by_source = {
        source_id: entry["entity_id"]
        for entry in registry.get("buildings", {}).values()
        if entry.get("available_lods", {}).get("1", {}).get("status") == "APPROVED"
        for source_id in entry.get("source_feature_ids", [])
    }
    for feature in renderables:
        props = feature["properties"]
        detailed_id = detailed_by_source.get(props["id"]) or detailed_by_source.get(props["canonical_entity_id"])
        if detailed_id:
            props["detailed_asset_id"] = detailed_id

    seen: set[str] = set()
    for feature in raw_buildings:
        props = feature["properties"]
        entity_id = props["id"]
        if entity_id in seen:
            anomalies.append({"entity_id": entity_id, "category": "PIPELINE_ERROR", "issue": "duplicate_entity_id"})
        seen.add(entity_id)
        height, base = float(props["height_m"]), float(props.get("min_height_m", 0))
        if height <= base:
            anomalies.append({"entity_id": entity_id, "category": "SOURCE_DATA_ISSUE", "issue": "non_positive_extrusion", "height_m": height, "min_height_m": base})
        if height > 350:
            anomalies.append({"entity_id": entity_id, "category": "SOURCE_DATA_ISSUE", "issue": "extreme_height", "height_m": height})
        if not boundary.covers(shape(feature["geometry"]).representative_point()):
            anomalies.append({"entity_id": entity_id, "category": "PIPELINE_ERROR", "issue": "outside_working_boundary"})

    def indices(point) -> tuple[int, int]:
        return math.floor((point.x - origin_x) / args.tile_size), math.floor((point.y - origin_y) / args.tile_size)

    canonical_tile = {entity_id: tile_id(*indices(geometry.centroid)) for entity_id, geometry in canonical_owner_geometry.items()}
    grouped: dict[str, list[dict[str, Any]]] = {}
    for feature in renderables:
        grouped.setdefault(canonical_tile[feature["properties"]["canonical_entity_id"]], []).append(feature)

    context = {key: payload["features"] for key, payload in datasets.items() if key in {"roads", "paths", "open_spaces"}}
    all_tile_ids = set(grouped)
    for key, features in context.items():
        for feature in features:
            geometry = shape(feature["geometry"])
            gx0, gy0, gx1, gy1 = geometry.bounds
            for column in range(math.floor((gx0 - origin_x) / args.tile_size), math.floor((gx1 - origin_x) / args.tile_size) + 1):
                for row in range(math.floor((gy0 - origin_y) / args.tile_size), math.floor((gy1 - origin_y) / args.tile_size) + 1):
                    cell = box(origin_x + column * args.tile_size, origin_y + row * args.tile_size, origin_x + (column + 1) * args.tile_size, origin_y + (row + 1) * args.tile_size)
                    if boundary.intersects(cell) and geometry.intersects(cell):
                        all_tile_ids.add(tile_id(column, row))

    TILE_INPUTS.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    tiles = []
    for current_id in sorted(all_tile_ids):
        _, column_text, row_text = current_id.split("_")
        column, row = int(column_text), int(row_text)
        bounds = [origin_x + column * args.tile_size, origin_y + row * args.tile_size, origin_x + (column + 1) * args.tile_size, origin_y + (row + 1) * args.tile_size]
        cell = box(*bounds)
        tile_context: dict[str, list[dict[str, Any]]] = {}
        for key, features in context.items():
            clipped = []
            for feature in features:
                intersection = make_valid(shape(feature["geometry"]).intersection(cell))
                if not intersection.is_empty:
                    clipped.append(feature_copy(feature, intersection))
            tile_context[key] = clipped
        tile_buildings = sorted(grouped.get(current_id, []), key=lambda item: (item["properties"]["canonical_entity_id"], item["properties"]["id"]))
        entities = sorted({feature["properties"]["canonical_entity_id"] for feature in tile_buildings})
        payload = {
            "schema_version": 1,
            "pipeline_version": PIPELINE_VERSION,
            "tile_id": current_id,
            "tile_size_m": args.tile_size,
            "bounds": bounds,
            "source_sha256": source_hash,
            "ground": clean_mapping(make_valid(boundary.intersection(cell))),
            "buildings": tile_buildings,
            **tile_context,
        }
        input_hash = hashlib.sha256(stable_json(payload)).hexdigest()
        payload["input_sha256"] = input_hash
        path = TILE_INPUTS / f"{current_id}.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        tiles.append({
            "tile_id": current_id,
            "bounds": bounds,
            "center": [(bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2],
            "asset_path": f"tiles/{current_id}.glb",
            "input_path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "input_sha256": input_hash,
            "building_count": len(entities),
            "render_volume_count": len(tile_buildings),
            "entities": entities,
            "triangle_count": None,
            "mesh_count": None,
            "material_count": None,
            "bytes": None,
            "status": "PENDING",
        })

    audit = read("bgc-data-audit.json")
    manifest = {
        "schema_version": 1,
        "world_id": "bgc-whole-city-lod2-v1",
        "pipeline_version": PIPELINE_VERSION,
        "source_sha256": source_hash,
        "tile_strategy": {"type": "fixed_local_meter_grid", "size_m": args.tile_size, "ownership": "canonical building centroid; parts follow containing outline"},
        "boundary": {"bounds": list(boundary.bounds), "area_m2": round(boundary.area, 2)},
        "representation": "MERGED_BY_TILE_MATERIAL_WITH_ENTITY_SIDECAR",
        "tile_loading": "ALL_LOADED",
        "height_coverage_percent": audit.get("height_coverage_percent", {}),
        "tiles": tiles,
        "totals": {"tiles": len(tiles), "canonical_buildings": len(canonical_owner_geometry), "building_outlines": len(outlines), "building_parts": len(parts), "render_volumes": len(renderables)},
        "anomalies": anomalies,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"BGC_TILES: tiles={len(tiles)} canonical_buildings={len(canonical_owner_geometry)} render_volumes={len(renderables)} anomalies={len(anomalies)}")


if __name__ == "__main__":
    main()
