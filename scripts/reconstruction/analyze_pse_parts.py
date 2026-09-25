"""Deterministic geographic analysis of mapped PSE footprint relationships.

OSM polygons are verified geographic data, not proof of architectural stacking.
Run with the pinned project Python environment. No network or Blender required.
"""

from __future__ import annotations

import json
from pathlib import Path

from shapely.geometry import shape


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data/reconstruction_packages/bgc_m17_0003/geometry.geojson"
OUTPUT = ROOT / "data/reports/pse-part-analysis.json"


def round_value(value: float) -> float:
    return round(float(value), 4)


def analyze() -> dict:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    features = sorted(source["features"], key=lambda item: item["id"])
    polygons = {item["id"]: shape(item["geometry"]) for item in features}
    if any(not polygon.is_valid for polygon in polygons.values()):
        raise ValueError("PSE source contains an invalid polygon")
    records = []
    for item in features:
        source_id = item["id"]
        polygon = polygons[source_id]
        rectangle = polygon.minimum_rotated_rectangle
        edges = list(rectangle.exterior.coords)
        longest = max(((b[0] - a[0], b[1] - a[1]) for a, b in zip(edges, edges[1:])),
                      key=lambda edge: edge[0] ** 2 + edge[1] ** 2)
        import math
        axis_bearing = math.degrees(math.atan2(longest[0], longest[1])) % 180
        relationships = []
        for other_id, other in polygons.items():
            if other_id == source_id:
                continue
            overlap = polygon.intersection(other).area
            self_fraction = overlap / polygon.area
            other_fraction = overlap / other.area
            if self_fraction < .01 and other_fraction < .01:
                label = "DISJOINT"
            elif other_fraction >= .95 and self_fraction < .95:
                label = "MOSTLY_CONTAINS"
            elif self_fraction >= .95 and other_fraction < .95:
                label = "MOSTLY_CONTAINED"
            else:
                label = "PARTIAL_OVERLAP"
            relationships.append({
                "other_source_id": other_id,
                "relationship": label,
                "intersection_m2": round_value(overlap),
                "self_fraction_inside_other": round_value(self_fraction),
                "other_fraction_inside_self": round_value(other_fraction),
                "shared_boundary_m": round_value(polygon.boundary.intersection(other.boundary).length),
                "self_difference_m2": round_value(polygon.difference(other).area),
            })
        records.append({
            "source_id": source_id,
            "height_m": item["properties"].get("height_m"),
            "area_m2": round_value(polygon.area),
            "perimeter_m": round_value(polygon.length),
            "centroid_m": [round_value(polygon.centroid.x), round_value(polygon.centroid.y)],
            "bounds_m": [round_value(value) for value in polygon.bounds],
            "principal_axis_bearing_deg_clockwise_from_north_mod_180": round_value(axis_bearing),
            "relationships": relationships,
        })
    body = polygons["osm:way:538701627"]
    frontpiece = polygons["osm:way:1069827306"]
    residual = body.difference(frontpiece)
    if residual.geom_type != "Polygon" or residual.interiors:
        raise ValueError("PSE body partition no longer yields one simple polygon")
    return {
        "schema_version": 1,
        "source": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
        "evidence_state": "VERIFIED_GEOGRAPHIC",
        "thresholds": {"disjoint_overlap_fraction_below": .01,
                       "mostly_contained_fraction_at_least": .95},
        "interpretation_limit": "Footprint overlap does not establish floors, facade depth, roof shape, or component identity.",
        "parts": records,
        "massing_partition_hypothesis": {
            "evidence_state": "INFERRED",
            "description": "Extrude the 119.2 m body residual and the nested 131 m frontpiece separately to remove coincident volumes; architectural identity requires photo review.",
            "body_source_id": "osm:way:538701627",
            "frontpiece_source_id": "osm:way:1069827306",
            "body_residual_area_m2": round_value(residual.area),
            "body_residual_ring_m": [[round_value(x), round_value(y)] for x, y in residual.exterior.coords],
        },
    }


def main() -> None:
    OUTPUT.write_text(json.dumps(analyze(), indent=2) + "\n", encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
