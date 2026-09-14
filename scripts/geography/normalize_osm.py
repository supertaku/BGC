"""Normalize an immutable Overpass snapshot into canonical local-metre GeoJSON."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import re
import sys
from typing import Any

from shapely import make_valid, set_precision
from shapely.affinity import translate
from shapely.geometry import (
    GeometryCollection,
    LineString,
    MultiLineString,
    MultiPolygon,
    Point,
    Polygon,
    mapping,
    shape,
)
from shapely.geometry.polygon import orient
from shapely.ops import polygonize, transform, unary_union

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from fetch_osm import file_sha256
from geo_utils import ORIGIN_PROJECTED, ORIGIN_WGS84, PROJECTED_CRS, SOURCE_CRS, _TRANSFORMER


ROOT = Path(__file__).resolve().parents[2]
PILOT_PATH = ROOT / "data" / "geographic" / "pilot-boundary.geojson"
RAW_DIR = ROOT / "data" / "raw" / "osm"
OUTPUT_DIR = ROOT / "data" / "processed"
LEVEL_HEIGHT_M = 3.2
TAG_KEYS = {
    "name", "alt_name", "short_name", "building", "building:part", "height",
    "min_height", "building:levels", "building:min_level", "building:material",
    "building:colour", "roof:shape", "roof:height", "roof:levels", "highway",
    "width", "lanes", "surface", "sidewalk", "footway", "crossing", "area",
    "leisure", "amenity", "natural", "barrier", "landuse", "shop", "wikidata",
    "wikipedia", "operator", "layer", "type",
}
PATH_CLASSES = {"footway", "pedestrian", "path", "steps", "cycleway", "bridleway", "corridor"}
OPEN_SPACE_LEISURE = {"park", "garden", "playground", "pitch", "recreation_ground"}
OPEN_SPACE_LANDUSE = {"grass", "recreation_ground", "village_green", "forest", "meadow"}


def is_open_space(tags: dict[str, str]) -> bool:
    return (
        tags.get("leisure") in OPEN_SPACE_LEISURE
        or tags.get("landuse") in OPEN_SPACE_LANDUSE
        or tags.get("natural") in {"wood", "scrub", "grassland"}
    )


def select_snapshot(explicit: Path | None) -> tuple[Path, Path, dict[str, Any]]:
    if explicit:
        raw_path = explicit.resolve()
        meta_path = raw_path.with_name(raw_path.name.replace(".json", ".meta.json"))
    else:
        metas = sorted(RAW_DIR.glob("pilot-*.meta.json"), reverse=True)
        if not metas:
            raise FileNotFoundError("No immutable pilot OSM snapshot; run scripts/geography/fetch_osm.py")
        meta_path = metas[0]
        raw_path = meta_path.with_name(meta_path.name.replace(".meta.json", ".json"))
    if not raw_path.is_file() or not meta_path.is_file():
        raise FileNotFoundError(f"Snapshot pair is incomplete: {raw_path}, {meta_path}")
    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    if file_sha256(raw_path) != metadata.get("sha256"):
        raise RuntimeError(f"Snapshot hash mismatch: {raw_path}")
    return raw_path, meta_path, metadata


def retained_tags(tags: dict[str, str]) -> dict[str, str]:
    return {
        key: value for key, value in tags.items()
        if key in TAG_KEYS or key.startswith("addr:")
    }


def coordinates_from_geometry(geometry: list[dict[str, Any]] | None) -> list[tuple[float, float]]:
    if not geometry:
        return []
    return [(float(point["lon"]), float(point["lat"])) for point in geometry if "lon" in point and "lat" in point]


def polygonal_only(geometry):
    if geometry.is_empty:
        return GeometryCollection()
    if isinstance(geometry, (Polygon, MultiPolygon)):
        return geometry
    if isinstance(geometry, GeometryCollection):
        polygons = [part for part in geometry.geoms if isinstance(part, (Polygon, MultiPolygon))]
        return unary_union(polygons) if polygons else GeometryCollection()
    return GeometryCollection()


def checked_polygon(coords: list[tuple[float, float]], issue: dict[str, Any]):
    if len(coords) < 4 or coords[0] != coords[-1]:
        issue["reason"] = "open_or_short_ring"
        return GeometryCollection()
    polygon = Polygon(coords)
    if polygon.is_valid:
        return polygon
    repaired = polygonal_only(make_valid(polygon))
    issue["reason"] = "invalid_polygon"
    issue["repair"] = "shapely.make_valid" if not repaired.is_empty else "rejected"
    return repaired


def relation_polygon(element: dict[str, Any], issues: list[dict[str, Any]]):
    role_lines: dict[str, list[LineString]] = defaultdict(list)
    for member in element.get("members", []):
        if member.get("type") != "way":
            continue
        coords = coordinates_from_geometry(member.get("geometry"))
        if len(coords) >= 2:
            role = member.get("role") or "outer"
            role_lines[role].append(LineString(coords))

    def assemble(lines: list[LineString]):
        return unary_union(list(polygonize(unary_union(lines)))) if lines else GeometryCollection()

    outer = assemble(role_lines.get("outer", []) + role_lines.get("outline", []))
    inner = assemble(role_lines.get("inner", []))
    result = polygonal_only(outer.difference(inner) if not inner.is_empty else outer)
    if result.is_empty:
        issues.append({"source_id": f"osm:relation:{element['id']}", "reason": "relation_polygon_assembly_failed", "repair": "rejected"})
    elif not result.is_valid:
        result = polygonal_only(make_valid(result))
        issues.append({"source_id": f"osm:relation:{element['id']}", "reason": "invalid_relation_polygon", "repair": "shapely.make_valid"})
    return result


def to_local(geometry):
    projected = transform(_TRANSFORMER.transform, geometry)
    return translate(projected, xoff=-ORIGIN_PROJECTED[0], yoff=-ORIGIN_PROJECTED[1])


def oriented(geometry):
    if isinstance(geometry, Polygon):
        return orient(geometry, sign=1.0)
    if isinstance(geometry, MultiPolygon):
        return MultiPolygon([orient(part, sign=1.0) for part in geometry.geoms])
    return geometry


def rounded(value):
    if isinstance(value, (tuple, list)):
        return [rounded(child) for child in value]
    if isinstance(value, float):
        return round(value, 3)
    return value


def mapped(geometry) -> dict[str, Any]:
    geometry = set_precision(geometry, grid_size=0.001, mode="valid_output")
    result = mapping(oriented(geometry))
    result["coordinates"] = rounded(result["coordinates"])
    return result


def parse_number(value: str | None) -> float | None:
    if value is None:
        return None
    match = re.fullmatch(r"\s*([0-9]+(?:\.[0-9]+)?)\s*", value)
    return float(match.group(1)) if match else None


def parse_height_value(value: str | None) -> float | None:
    if value is None:
        return None
    match = re.fullmatch(r"\s*([0-9]+(?:\.[0-9]+)?)\s*(m|metres?|meters?|ft|feet|')?\s*", value, re.IGNORECASE)
    if not match:
        return None
    amount = float(match.group(1))
    return amount * 0.3048 if (match.group(2) or "").lower() in {"ft", "feet", "'"} else amount


def height_observation(tags: dict[str, str]) -> dict[str, Any]:
    explicit = parse_height_value(tags.get("height"))
    levels = parse_number(tags.get("building:levels"))
    if explicit and 0.2 <= explicit <= 500:
        return {"height_m": round(explicit, 3), "status": "VERIFIED_GEOGRAPHIC", "method": "osm_height", "confidence": 0.75, "source_height": tags.get("height"), "source_levels": levels}
    if levels and 0 < levels <= 150:
        return {"height_m": round(levels * LEVEL_HEIGHT_M, 3), "status": "ESTIMATED", "method": f"building_levels_x_{LEVEL_HEIGHT_M:g}m", "confidence": 0.55, "source_height": tags.get("height"), "source_levels": levels}
    fallback = 0.6 if tags.get("building") == "roof" else 4.0 if tags.get("building:part") == "column" else 12.0
    return {"height_m": fallback, "status": "PROCEDURAL", "method": "diagnostic_type_fallback", "confidence": 0.15, "source_height": tags.get("height"), "source_levels": levels}


def min_height_observation(tags: dict[str, str]) -> dict[str, Any]:
    explicit = parse_height_value(tags.get("min_height"))
    min_level = parse_number(tags.get("building:min_level"))
    if explicit is not None:
        return {"min_height_m": round(explicit, 3), "status": "VERIFIED_GEOGRAPHIC", "method": "osm_min_height", "source_min_level": min_level}
    if min_level is not None:
        return {"min_height_m": round(min_level * LEVEL_HEIGHT_M, 3), "status": "ESTIMATED", "method": f"building_min_level_x_{LEVEL_HEIGHT_M:g}m", "source_min_level": min_level}
    return {"min_height_m": 0.0, "status": "UNKNOWN", "method": "ground_default", "source_min_level": min_level}


def building_feature(element: dict[str, Any], geometry, feature_kind: str, parent_ids: list[str] | None = None) -> dict[str, Any]:
    tags = element.get("tags", {})
    height = height_observation(tags)
    base = min_height_observation(tags)
    local = to_local(geometry)
    properties = {
        "id": f"osm:{element['type']}:{element['id']}",
        "source_ids": [f"osm:{element['type']}:{element['id']}", "source:osm"],
        "parent_ids": parent_ids or [],
        "name": tags.get("name"),
        "feature_kind": feature_kind,
        "height_m": height["height_m"],
        "min_height_m": base["min_height_m"],
        "levels": height["source_levels"],
        "height_status": height["status"],
        "height_method": height["method"],
        "height_confidence": height["confidence"],
        "footprint_status": "VERIFIED_GEOGRAPHIC",
        "footprint_confidence": 0.8,
        "material": tags.get("building:material"),
        "colour": tags.get("building:colour"),
        "footprint_area_m2": round(local.area, 2),
        "tags": retained_tags(tags),
    }
    return {"type": "Feature", "id": properties["id"], "properties": properties, "geometry": mapped(local)}


def road_width(tags: dict[str, str], is_path: bool) -> tuple[float, str, str]:
    explicit = parse_height_value(tags.get("width"))
    if explicit and 0.3 <= explicit <= 60:
        return explicit, "VERIFIED_GEOGRAPHIC", "osm_width"
    highway = tags.get("highway", "")
    if is_path:
        value = {"pedestrian": 5.0, "steps": 2.0, "cycleway": 2.5}.get(highway, 1.8)
        return value, "ESTIMATED", "path_class_default"
    lanes = parse_number(tags.get("lanes"))
    if lanes and 0 < lanes <= 12:
        return lanes * 3.2, "ESTIMATED", "lanes_x_3.2m"
    value = {
        "primary": 12.0, "secondary": 10.0, "tertiary": 8.0,
        "residential": 6.5, "service": 5.0, "living_street": 5.0,
    }.get(highway, 5.0)
    return value, "ESTIMATED", "highway_class_default"


def linear_feature(element: dict[str, Any], pilot, is_path: bool) -> dict[str, Any] | None:
    coords = coordinates_from_geometry(element.get("geometry"))
    if len(coords) < 2:
        return None
    tags = element.get("tags", {})
    line = LineString(coords).intersection(pilot)
    if line.is_empty:
        return None
    local_line = to_local(line)
    width, width_status, width_method = road_width(tags, is_path)
    is_area = tags.get("area") == "yes" and len(coords) >= 4 and coords[0] == coords[-1]
    if is_area:
        source_polygon = Polygon(coords).intersection(pilot)
        surface = to_local(source_polygon)
        surface_status = "VERIFIED_GEOGRAPHIC"
        surface_method = "osm_area_geometry"
    else:
        surface = local_line.buffer(width / 2.0, cap_style="flat", join_style="round")
        surface_status = "ESTIMATED"
        surface_method = "buffered_centerline"
    if surface.is_empty:
        return None
    source_id = f"osm:{element['type']}:{element['id']}"
    properties = {
        "id": source_id,
        "source_ids": [source_id, "source:osm"],
        "name": tags.get("name"),
        "class": tags.get("highway"),
        "width_m": round(width, 3),
        "width_status": width_status,
        "width_method": width_method,
        "surface_status": surface_status,
        "surface_method": surface_method,
        "centerline_length_m": round(local_line.length, 2),
        "centerline_local": mapped(local_line),
        "tags": retained_tags(tags),
    }
    return {"type": "Feature", "id": source_id, "properties": properties, "geometry": mapped(surface)}


def area_feature(element: dict[str, Any], geometry, category: str) -> dict[str, Any]:
    local = to_local(geometry)
    tags = element.get("tags", {})
    source_id = f"osm:{element['type']}:{element['id']}"
    properties = {
        "id": source_id,
        "source_ids": [source_id, "source:osm"],
        "name": tags.get("name"),
        "category": category,
        "geometry_status": "VERIFIED_GEOGRAPHIC",
        "area_m2": round(local.area, 2),
        "tags": retained_tags(tags),
    }
    return {"type": "Feature", "id": source_id, "properties": properties, "geometry": mapped(local)}


def feature_collection(dataset_id: str, features: list[dict[str, Any]], metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "FeatureCollection",
        "name": dataset_id,
        "schema_version": 2,
        "dataset_id": dataset_id,
        "source_id": "source:osm",
        "source_sha256": metadata["sha256"],
        "source_retrieved_at": metadata["retrieved_at"],
        "source_crs": SOURCE_CRS.to_string(),
        "projected_crs": PROJECTED_CRS.to_string(),
        "local_frame": {
            "origin_wgs84": {"longitude": ORIGIN_WGS84[0], "latitude": ORIGIN_WGS84[1]},
            "origin_projected": {"easting": round(ORIGIN_PROJECTED[0], 3), "northing": round(ORIGIN_PROJECTED[1], 3)},
            "axes": {"x": "east", "y": "north", "z": "up"},
            "units": "metres",
            "transform_library": "pyproj",
        },
        "features": features,
    }


def write_collection(name: str, features: list[dict[str, Any]], metadata: dict[str, Any]) -> None:
    path = OUTPUT_DIR / f"{name}.geojson"
    path.write_text(json.dumps(feature_collection(name, features, metadata), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_dissolved_surface(name: str, source_name: str, features: list[dict[str, Any]], metadata: dict[str, Any]) -> None:
    if not features:
        write_collection(name, [], metadata)
        return
    surface = polygonal_only(make_valid(unary_union([shape(feature["geometry"]) for feature in features])))
    feature = {
        "type": "Feature",
        "id": f"derived:{name}",
        "properties": {
            "id": f"derived:{name}",
            "source_dataset": source_name,
            "source_feature_count": len(features),
            "geometry_status": "INFERRED",
            "method": "shapely_unary_union_of_normalized_surfaces",
        },
        "geometry": mapped(surface),
    }
    write_collection(name, [feature], metadata)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--boundary", type=Path, default=PILOT_PATH)
    parser.add_argument("--output-prefix", default="pilot")
    args = parser.parse_args()
    prefix = args.output_prefix
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", prefix):
        raise ValueError("--output-prefix must be a lowercase filename-safe identifier")
    raw_path, meta_path, metadata = select_snapshot(args.snapshot)
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    pilot_payload = json.loads(args.boundary.resolve().read_text(encoding="utf-8"))
    pilot = shape(pilot_payload["features"][0]["geometry"])
    elements = raw.get("elements", [])
    ways = {element["id"]: element for element in elements if element.get("type") == "way"}
    issues: list[dict[str, Any]] = []
    buildings: list[dict[str, Any]] = []
    roads: list[dict[str, Any]] = []
    paths: list[dict[str, Any]] = []
    open_spaces: list[dict[str, Any]] = []
    pois: list[dict[str, Any]] = []
    suppressed_building_ways: set[int] = set()
    used_area_relations: set[int] = set()

    for relation in (element for element in elements if element.get("type") == "relation"):
        tags = relation.get("tags", {})
        relation_id = f"osm:relation:{relation['id']}"
        if tags.get("type") == "building":
            for member in relation.get("members", []):
                if member.get("type") != "way" or member.get("role") not in {"outline", "part"}:
                    continue
                coords = coordinates_from_geometry(member.get("geometry"))
                member_element = ways.get(member["ref"], {"type": "way", "id": member["ref"], "tags": {}})
                issue = {"source_id": f"osm:way:{member['ref']}"}
                geometry = checked_polygon(coords, issue)
                if "reason" in issue:
                    issues.append(issue)
                if geometry.is_empty or not pilot.covers(geometry.representative_point()):
                    continue
                merged = dict(member_element)
                if member.get("role") == "outline":
                    merged["tags"] = {**relation.get("tags", {}), **member_element.get("tags", {})}
                buildings.append(building_feature(merged, geometry, "building_part" if member.get("role") == "part" else "building_outline", [relation_id]))
                suppressed_building_ways.add(member["ref"])
            continue

        if tags.get("type") == "multipolygon" and ("building" in tags or "building:part" in tags):
            geometry = relation_polygon(relation, issues)
            if not geometry.is_empty and pilot.covers(geometry.representative_point()):
                kind = "building_part" if "building:part" in tags else "building_outline"
                buildings.append(building_feature(relation, geometry, kind))
                suppressed_building_ways.update(member["ref"] for member in relation.get("members", []) if member.get("type") == "way")
            continue

        if tags.get("type") == "multipolygon" and is_open_space(tags):
            geometry = relation_polygon(relation, issues).intersection(pilot)
            if not geometry.is_empty:
                category = tags.get("leisure") or tags.get("natural") or tags.get("landuse") or "open_space"
                open_spaces.append(area_feature(relation, geometry, category))
                used_area_relations.add(relation["id"])

    for element in elements:
        tags = element.get("tags", {})
        element_type = element.get("type")
        if element_type == "way" and ("building" in tags or "building:part" in tags) and element["id"] not in suppressed_building_ways:
            issue = {"source_id": f"osm:way:{element['id']}"}
            geometry = checked_polygon(coordinates_from_geometry(element.get("geometry")), issue)
            if "reason" in issue:
                issues.append(issue)
            if not geometry.is_empty and pilot.covers(geometry.representative_point()) and geometry.area > 1e-10:
                kind = "building_part" if "building:part" in tags else "building_outline"
                buildings.append(building_feature(element, geometry, kind))

        if element_type == "way" and "highway" in tags:
            is_path = tags.get("highway") in PATH_CLASSES
            feature = linear_feature(element, pilot, is_path)
            if feature:
                (paths if is_path else roads).append(feature)

        if element_type == "way" and any(key in tags for key in ("leisure", "natural", "landuse")):
            coords = coordinates_from_geometry(element.get("geometry"))
            if len(coords) >= 4 and coords[0] == coords[-1]:
                geometry = checked_polygon(coords, {"source_id": f"osm:way:{element['id']}"}).intersection(pilot)
                category = tags.get("leisure") or tags.get("natural") or tags.get("landuse") or "open_space"
                if not geometry.is_empty and is_open_space(tags):
                    open_spaces.append(area_feature(element, geometry, category))

        if any(key in tags for key in ("amenity", "shop", "leisure", "natural", "barrier")) or tags.get("highway") == "street_lamp":
            point = None
            if element_type == "node" and "lon" in element and "lat" in element:
                point = Point(float(element["lon"]), float(element["lat"]))
            elif element_type == "way":
                coords = coordinates_from_geometry(element.get("geometry"))
                if coords:
                    point = (Polygon(coords).representative_point() if len(coords) >= 4 and coords[0] == coords[-1] else LineString(coords).interpolate(0.5, normalized=True))
            elif element_type == "relation" and element.get("id") in used_area_relations:
                geometry = relation_polygon(element, [])
                if not geometry.is_empty:
                    point = geometry.representative_point()
            if point is not None and pilot.covers(point):
                local_point = to_local(point)
                source_id = f"osm:{element_type}:{element['id']}"
                pois.append({
                    "type": "Feature", "id": source_id,
                    "properties": {
                        "id": source_id, "source_ids": [source_id, "source:osm"],
                        "name": tags.get("name"),
                        "category": tags.get("amenity") or tags.get("shop") or tags.get("leisure") or tags.get("natural") or tags.get("barrier") or tags.get("highway"),
                        "geometry_status": "VERIFIED_GEOGRAPHIC",
                        "tags": retained_tags(tags),
                    },
                    "geometry": mapped(local_point),
                })

    for collection in (buildings, roads, paths, open_spaces, pois):
        collection.sort(key=lambda feature: feature["properties"]["id"])
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_collection(f"{prefix}-buildings", buildings, metadata)
    write_collection(f"{prefix}-roads", roads, metadata)
    write_collection(f"{prefix}-paths", paths, metadata)
    write_collection(f"{prefix}-open-spaces", open_spaces, metadata)
    write_collection(f"{prefix}-pois", pois, metadata)
    write_dissolved_surface(f"{prefix}-road-surfaces", f"{prefix}-roads", roads, metadata)
    write_dissolved_surface(f"{prefix}-path-surfaces", f"{prefix}-paths", paths, metadata)
    write_dissolved_surface(f"{prefix}-open-space-surfaces", f"{prefix}-open-spaces", open_spaces, metadata)
    boundary_local = to_local(pilot)
    boundary_feature = {
        "type": "Feature",
        "id": pilot_payload["features"][0]["id"],
        "properties": {
            "id": pilot_payload["features"][0]["id"],
            "name": pilot_payload["features"][0]["properties"]["name"],
            "boundary_status": pilot_payload["features"][0]["properties"]["status"],
            "area_m2": round(boundary_local.area, 2),
        },
        "geometry": mapped(boundary_local),
    }
    write_collection(f"{prefix}-boundary-local", [boundary_feature], metadata)
    boundary_local = {
        "type": "Feature",
        "id": pilot_payload["features"][0].get("id", "scope:pilot"),
        "properties": {
            **pilot_payload["features"][0].get("properties", {}),
            "geometry_status": "ESTIMATED",
            "source_ids": pilot_payload["features"][0].get("properties", {}).get("sources", []),
        },
        "geometry": mapped(to_local(pilot)),
    }
    write_collection(f"{prefix}-boundary-local", [boundary_local], metadata)

    heights = Counter(feature["properties"]["height_status"] for feature in buildings)
    audit = {
        "schema_version": 1,
        "source_snapshot": str(raw_path.relative_to(ROOT)).replace("\\", "/"),
        "source_metadata": str(meta_path.relative_to(ROOT)).replace("\\", "/"),
        "source_sha256": metadata["sha256"],
        "counts": {
            "building_outlines": sum(feature["properties"]["feature_kind"] == "building_outline" for feature in buildings),
            "building_parts": sum(feature["properties"]["feature_kind"] == "building_part" for feature in buildings),
            "buildings_named": sum(bool(feature["properties"].get("name")) for feature in buildings),
            "heights_verified_geographic": heights["VERIFIED_GEOGRAPHIC"],
            "heights_estimated": heights["ESTIMATED"],
            "heights_procedural": heights["PROCEDURAL"],
            "roads": len(roads), "paths": len(paths), "open_spaces": len(open_spaces), "pois": len(pois),
        },
        "issues": issues,
    }
    total_heights = len(buildings) or 1
    audit["height_coverage_percent"] = {
        "VERIFIED_GEOGRAPHIC": round(100 * heights["VERIFIED_GEOGRAPHIC"] / total_heights, 2),
        "ESTIMATED": round(100 * heights["ESTIMATED"] / total_heights, 2),
        "PROCEDURAL": round(100 * heights["PROCEDURAL"] / total_heights, 2),
    }
    audit["boundary"] = {
        "path": str(args.boundary.resolve().relative_to(ROOT)).replace("\\", "/"),
        "area_m2": round(to_local(pilot).area, 2),
        "bounds_wgs84": [round(value, 7) for value in pilot.bounds],
    }
    (OUTPUT_DIR / f"{prefix}-data-audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "BGC_NORMALIZE: "
        f"buildings={len(buildings)} roads={len(roads)} paths={len(paths)} "
        f"open_spaces={len(open_spaces)} pois={len(pois)} issues={len(issues)}"
    )


if __name__ == "__main__":
    main()
