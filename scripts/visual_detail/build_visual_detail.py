"""Build small, evidence-labelled, tile-owned High Street detail data.

All positions come from the pinned processed OSM snapshot. The narrow decorative
bands and furniture spacing are explicitly inferred, not surveyed site details.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from shapely.geometry import Point, box, shape


ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
OUTPUT = ROOT / "web" / "components" / "runtime" / "visual-detail.json"
PARK_IDS = {"osm:way:174398019", "osm:way:145147836"}
CORE = box(-540, -220, 230, 220)


def features(name: str):
    return json.loads((PROCESSED / name).read_text(encoding="utf-8"))["features"]


def polygons(geometry):
    if geometry.is_empty:
        return []
    if geometry.geom_type == "Polygon":
        return [geometry]
    if geometry.geom_type == "MultiPolygon":
        return list(geometry.geoms)
    return []


def ring(points):
    return [[round(x, 2), round(y, 2)] for x, y in list(points)[:-1]]


def encode(geometry):
    return {"outer": ring(geometry.exterior.coords), "holes": [ring(h.coords) for h in geometry.interiors]}


def main():
    world = json.loads((ROOT / "web/public/world/bgc-world.json").read_text(encoding="utf-8"))
    tiles = [(tile["tile_id"], box(*tile["bounds"])) for tile in world["tiles"]]
    package = {"schema_version": 1, "source_snapshot": "c7c77bdee83947293624a3a6036089e809c2fb2c1cec4d5283fb1c89535a8ac3", "tiles": {}}

    def tile_record(tile_id):
        return package["tiles"].setdefault(tile_id, {"surfaces": {}, "instances": {}, "sources": []})

    def add_surface(feature_id, category, geom, grounding):
        if geom.is_empty:
            return
        for tile_id, extent in tiles:
            if not geom.intersects(extent):
                continue
            clipped = geom.intersection(extent)
            for poly in polygons(clipped):
                if poly.area < 0.25:
                    continue
                item = tile_record(tile_id)
                item["surfaces"].setdefault(category, []).append(encode(poly))
                item["sources"].append({"id": feature_id, "category": category, "grounding": grounding})

    def add_instance(feature_id, category, x, y, grounding):
        for tile_id, extent in tiles:
            if extent.covers(Point(x, y)):
                item = tile_record(tile_id)
                item["instances"].setdefault(category, []).append({"id": f"{feature_id}:{category}:{round(x, 1)}:{round(y, 1)}", "position": [round(x, 2), round(-y, 2)], "grounding": grounding})
                return

    paths = features("bgc-paths.geojson")
    path_union = []
    for feature in paths:
        props = feature["properties"]
        geom = shape(feature["geometry"])
        if not geom.intersects(CORE):
            continue
        tags = props.get("tags", {})
        if props.get("name") == "Bonifacio High Street" and geom.geom_type in ("Polygon", "MultiPolygon"):
            path_union.append(geom)
            # A narrow paving border makes the mapped pedestrian spine read as a plaza.
            add_surface(props["id"], "PAVING_BORDER", geom.difference(geom.buffer(-0.55)), "INFERRED")
        if tags.get("crossing") == "zebra" and geom.geom_type in ("Polygon", "MultiPolygon"):
            add_surface(props["id"], "ZEBRA_CROSSING", geom, "VERIFIED_GEOGRAPHIC")

    for feature in features("bgc-open-spaces.geojson"):
        props = feature["properties"]
        if props["id"] not in PARK_IDS:
            continue
        geom = shape(feature["geometry"])
        add_surface(props["id"], "PARK_EDGE", geom.difference(geom.buffer(-0.65)), "INFERRED")
        # Repeated grid is stable and sparse. It represents landscaped character only.
        xmin, ymin, xmax, ymax = geom.bounds
        for gx in range(math.floor(xmin / 14), math.ceil(xmax / 14) + 1):
            for gy in range(math.floor(ymin / 14), math.ceil(ymax / 14) + 1):
                seed = f"{props['id']}:{gx}:{gy}".encode()
                digest = hashlib.sha256(seed).digest()
                x = gx * 14 + (digest[0] / 255 - .5) * 4
                y = gy * 14 + (digest[1] / 255 - .5) * 4
                point = Point(x, y)
                if not geom.buffer(-3.5).covers(point):
                    continue
                if any(path.buffer(2.5).covers(point) for path in path_union):
                    continue
                if digest[2] < 115:
                    add_instance(props["id"], "TREE_CLUSTER", x, y, "INFERRED")
                elif digest[2] < 150:
                    add_instance(props["id"], "PLANTER_RECT", x, y, "INFERRED")

    # Sample selected High Street polygon boundaries. Each point stays near mapped
    # pedestrian space; exact furniture locations are deliberately marked inferred.
    for feature in paths:
        props = feature["properties"]
        if props.get("name") != "Bonifacio High Street":
            continue
        geom = shape(feature["geometry"])
        if geom.geom_type != "Polygon" or geom.area < 100 or not geom.intersects(CORE):
            continue
        boundary = geom.exterior
        for i in range(1, min(int(boundary.length // 22), 20)):
            point = boundary.interpolate(i * 22)
            if not CORE.covers(point):
                continue
            category = ("BENCH_LINEAR", "LIGHT_POLE_STANDARD", "PLANTER_RECT")[i % 3]
            add_instance(props["id"], category, point.x, point.y, "INFERRED")

    # Deduplicate source entries and provide compact counts for reproducible QA.
    for item in package["tiles"].values():
        item["sources"] = list({(s["id"], s["category"], s["grounding"]): s for s in item["sources"]}.values())
    package["counts"] = {
        "tiles": len(package["tiles"]),
        "surfaces": sum(sum(len(v) for v in t["surfaces"].values()) for t in package["tiles"].values()),
        "instances": sum(sum(len(v) for v in t["instances"].values()) for t in package["tiles"].values()),
    }
    OUTPUT.write_text(json.dumps(package, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}: {package['counts']}")


if __name__ == "__main__":
    main()
