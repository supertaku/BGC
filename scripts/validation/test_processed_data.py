"""Validate normalized pilot datasets and their provenance contract."""

from __future__ import annotations

import json
from pathlib import Path

from shapely.geometry import shape


ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"


def load(name: str) -> dict:
    path = PROCESSED / name
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["type"] == "FeatureCollection"
    assert payload["source_crs"] == "EPSG:4326"
    assert payload["projected_crs"] == "EPSG:32651"
    assert payload["local_frame"]["axes"] == {"x": "east", "y": "north", "z": "up"}
    assert payload["source_sha256"]
    return payload


def main() -> None:
    buildings = load("pilot-buildings.geojson")
    roads = load("pilot-roads.geojson")
    paths = load("pilot-paths.geojson")
    pois = load("pilot-pois.geojson")
    open_spaces = load("pilot-open-spaces.geojson")
    road_surfaces = load("pilot-road-surfaces.geojson")
    path_surfaces = load("pilot-path-surfaces.geojson")
    open_space_surfaces = load("pilot-open-space-surfaces.geojson")
    boundary = load("pilot-boundary-local.geojson")
    assert len(buildings["features"]) >= 10
    assert roads["features"] and paths["features"] and pois["features"] and open_spaces["features"]
    assert road_surfaces["features"] and path_surfaces["features"]
    assert open_space_surfaces["features"] and len(boundary["features"]) == 1
    seen: set[str] = set()
    for payload in (
        buildings,
        roads,
        paths,
        pois,
        open_spaces,
        road_surfaces,
        path_surfaces,
        open_space_surfaces,
        boundary,
    ):
        assert payload["source_sha256"] == buildings["source_sha256"]
        for feature in payload["features"]:
            properties = feature["properties"]
            local_id = properties.get("id") or properties.get("name")
            assert local_id
            identifier = f"{payload['dataset_id']}:{local_id}"
            assert identifier not in seen
            seen.add(identifier)
            geometry = shape(feature["geometry"])
            assert not geometry.is_empty and geometry.is_valid
            min_x, min_y, max_x, max_y = geometry.bounds
            assert max(abs(min_x), abs(min_y), abs(max_x), abs(max_y)) < 1000
    for feature in buildings["features"]:
        properties = feature["properties"]
        assert properties["height_status"] in {"VERIFIED_GEOGRAPHIC", "ESTIMATED", "PROCEDURAL"}
        assert 0 < properties["height_m"] <= 500
        assert properties["footprint_status"] == "VERIFIED_GEOGRAPHIC"
        assert properties["source_ids"][0].startswith("osm:")
    print(
        "BGC_PROCESSED: PASS "
        f"buildings={len(buildings['features'])} roads={len(roads['features'])} "
        f"paths={len(paths['features'])} open_spaces={len(open_spaces['features'])} pois={len(pois['features'])}"
    )


if __name__ == "__main__":
    main()
