"""Build the compact, deterministic interaction and environment sidecar for M12-M14."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TILES_DIR = ROOT / "data" / "processed" / "bgc-tiles"
POIS_PATH = ROOT / "data" / "processed" / "bgc-pois.geojson"
BOUNDARY_PATH = ROOT / "data" / "processed" / "bgc-boundary-local.geojson"
WORLD_PATH = ROOT / "web" / "public" / "world" / "bgc-world.json"
OUTPUT_PATH = ROOT / "web" / "public" / "world" / "bgc-interactive.json"
OUTPUT_TILES_DIR = ROOT / "web" / "public" / "world" / "tiles"

ENVIRONMENT_CATEGORIES = {
    "tree": "TREE_GENERIC",
    "street_lamp": "STREET_LAMP_GENERIC",
    "bench": "BENCH_GENERIC",
    "bollard": "BOLLARD_GENERIC",
    "waste_basket": "WASTE_BIN_GENERIC",
    "shelter": "SHELTER_GENERIC",
}


def round_ring(ring: list[list[float]]) -> list[list[float]]:
    """Convert local east/north data to Three.js x/z and retain metre precision."""
    return [[round(point[0], 2), round(-point[1], 2)] for point in ring]


def polygon_rings(geometry: dict) -> list[list[list[float]]]:
    if geometry["type"] == "Polygon":
        return [round_ring(geometry["coordinates"][0])]
    if geometry["type"] == "MultiPolygon":
        return [round_ring(polygon[0]) for polygon in geometry["coordinates"]]
    return []


def ring_bounds(rings: list[list[list[float]]]) -> list[float]:
    points = [point for ring in rings for point in ring]
    return [
        round(min(point[0] for point in points), 2),
        round(min(point[1] for point in points), 2),
        round(max(point[0] for point in points), 2),
        round(max(point[1] for point in points), 2),
    ]


def centroid(rings: list[list[list[float]]]) -> list[float]:
    # A bbox centre is stable and sufficient for focus, LOD, and search navigation.
    bounds = ring_bounds(rings)
    return [round((bounds[0] + bounds[2]) / 2, 2), round((bounds[1] + bounds[3]) / 2, 2)]


def find_tile(point: list[float], tiles: list[dict]) -> str | None:
    x, north = point
    for tile in tiles:
        x0, y0, x1, y1 = tile["bounds"]
        if x0 <= x <= x1 and y0 <= north <= y1:
            return tile["tile_id"]
    return None


def main() -> None:
    world = json.loads(WORLD_PATH.read_text(encoding="utf-8"))
    registry = {
        asset["entity_id"]: asset for asset in world.get("detailed_assets", [])
    }
    tile_sidecars: dict[str, dict] = {}
    entities: dict[str, dict] = {}

    for tile_manifest in world["tiles"]:
        tile_id = tile_manifest["tile_id"]
        tile_data = json.loads((TILES_DIR / f"{tile_id}.json").read_text(encoding="utf-8"))
        footprints = []
        seen = set()
        for feature in tile_data.get("buildings", []):
            props = feature["properties"]
            entity_id = props.get("canonical_entity_id", props["id"])
            if entity_id in seen or props.get("feature_kind") == "building_part":
                continue
            rings = polygon_rings(feature["geometry"])
            if not rings:
                continue
            seen.add(entity_id)
            record = {
                "entity_id": entity_id,
                "name": props.get("name"),
                "aliases": sorted(
                    set(
                        value
                        for value in (
                            props.get("tags", {}).get("alt_name"),
                            props.get("tags", {}).get("short_name"),
                        )
                        if value
                    )
                ),
                "height_m": props.get("height_m"),
                "height_status": props.get("height_status", "UNKNOWN"),
                "building_type": (
                    "building"
                    if props.get("tags", {}).get("building") == "yes"
                    else props.get("tags", {}).get("building", "unknown")
                ),
                "detailed_asset_id": props.get("detailed_asset_id"),
                "tile_id": tile_id,
                "center": centroid(rings),
                "bounds": ring_bounds(rings),
                "rings": rings,
            }
            footprints.append(record)
            current = entities.get(entity_id)
            if current is None or (record["name"] and not current.get("name")):
                entities[entity_id] = {key: value for key, value in record.items() if key != "rings"}
        tile_sidecars[tile_id] = {"footprints": footprints, "environment": defaultdict(list)}

    pois = json.loads(POIS_PATH.read_text(encoding="utf-8"))["features"]
    counts: dict[str, int] = defaultdict(int)
    for feature in pois:
        category = feature["properties"].get("category")
        asset_type = ENVIRONMENT_CATEGORIES.get(category)
        if not asset_type or feature["geometry"].get("type") != "Point":
            continue
        coordinates = feature["geometry"]["coordinates"]
        tile_id = find_tile(coordinates, world["tiles"])
        if not tile_id:
            continue
        x, north = coordinates
        tile_sidecars[tile_id]["environment"][asset_type].append(
            {
                "id": feature["properties"]["id"],
                "position": [round(x, 2), round(-north, 2)],
                "grounding": "VERIFIED_GEOGRAPHIC",
            }
        )
        counts[asset_type] += 1

    boundary = json.loads(BOUNDARY_PATH.read_text(encoding="utf-8"))["features"][0]
    OUTPUT_TILES_DIR.mkdir(parents=True, exist_ok=True)
    for tile_id, data in sorted(tile_sidecars.items()):
        tile_payload = {
            "tile_id": tile_id,
            "footprints": data["footprints"],
            "environment": {
                asset_type: sorted(items, key=lambda item: item["id"])
                for asset_type, items in sorted(data["environment"].items())
            },
        }
        (OUTPUT_TILES_DIR / f"{tile_id}.json").write_text(
            json.dumps(tile_payload, separators=(",", ":"), ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    payload = {
        "schema_version": 1,
        "source_snapshot": "data/raw/osm/bgc-2026-09-14T162150Z.json",
        "source_status": "VERIFIED_GEOGRAPHIC",
        "boundary_status": boundary["properties"]["geometry_status"],
        "boundary": round_ring(boundary["geometry"]["coordinates"][0]),
        "tile_size_m": 250,
        "entities": sorted(
            (
                entity
                for entity in entities.values()
                if entity.get("name") or entity.get("detailed_asset_id")
            ),
            key=lambda item: item["entity_id"],
        ),
        "tile_sidecar_url_template": "/world/tiles/{tile_id}.json",
        "environment_counts": dict(sorted(counts.items())),
        "procedural_environment_count": 0,
        "lod1_entity_ids": sorted(registry),
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "INTERACTIVE_RUNTIME: "
        f"entities={len(entities)} tiles={len(tile_sidecars)} "
        f"environment={sum(counts.values())} bytes={OUTPUT_PATH.stat().st_size}"
    )


if __name__ == "__main__":
    main()
