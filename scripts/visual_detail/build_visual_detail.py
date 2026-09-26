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
from shapely import set_precision
from placement import Context, HEIGHTS, POLICY, boundary_frame
from collections import Counter


ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
OUTPUT = ROOT / "web/public/world/detail/high-street-public-realm.json"
PARK_IDS = {"osm:way:174398019", "osm:way:145147836"}
CORE = box(-540, -220, 230, 220)


def features(name: str):
    return json.loads((PROCESSED / name).read_text(encoding="utf-8"))["features"]


def polygons(geometry):
    if geometry.is_empty:
        return []
    if geometry.geom_type == "Polygon":
        return [geometry]
    if geometry.geom_type in ("MultiPolygon", "GeometryCollection"):
        return [p for child in geometry.geoms for p in polygons(child)]
    return []


def ring(points):
    return [[round(x, 2), round(y, 2)] for x, y in list(points)[:-1]]


def encode(geometry):
    return {"outer": ring(geometry.exterior.coords), "holes": [ring(h.coords) for h in geometry.interiors]}


def main():
    world = json.loads((ROOT / "web/public/world/bgc-world.json").read_text(encoding="utf-8"))
    tiles = [(tile["tile_id"], box(*tile["bounds"])) for tile in world["tiles"]]
    package = {"schema_version": 2, "dataset_id": "bgc-high-street-public-realm-v2", "coordinate_frame": "surfaces: east/north; instances: east/-north; metres", "surface_heights": HEIGHTS, "placement_policy": POLICY, "source_snapshot": "c7c77bdee83947293624a3a6036089e809c2fb2c1cec4d5283fb1c89535a8ac3", "tiles": {}}

    context = Context()
    candidates = []
    owners = {}
    stats = {}

    def tile_record(tile_id):
        return package["tiles"].setdefault(tile_id, {"surfaces": {}, "instances": {}, "sources": []})

    def add_surface(feature_id, category, geom, grounding, resolved_base=None):
        if resolved_base is None:
            remaining=geom
            for base, mask in [('PATH',context.path),('OPEN_SPACE',context.open),('ROAD',context.road)]:
                part=remaining.intersection(mask)
                add_surface(feature_id,category,part,grounding,base)
                remaining=remaining.difference(mask)
            add_surface(feature_id,category,remaining,grounding,'GROUND')
            return
        if geom.is_empty:
            return
        for tile_id, extent in tiles:
            if not geom.intersects(extent):
                continue
            clipped = set_precision(geom.intersection(extent), .01)
            for poly in polygons(clipped):
                if poly.area < 0.25:
                    continue
                item = tile_record(tile_id)
                record = encode(poly)
                base = resolved_base
                record.update(id=f"{feature_id}:{category}:{tile_id}:{hashlib.sha256(json.dumps(record,sort_keys=True).encode()).hexdigest()[:16]}", source_id=feature_id, category=category, grounding=grounding, base_surface=base, elevation_offset_m=HEIGHTS['DETAIL_EPSILON'])
                item["surfaces"].setdefault(category, []).append(record)
                item["sources"].append({"id": feature_id, "category": category, "grounding": grounding})

    def add_instance(feature_id, category, x, y, grounding, yaw=0, rule="PARK_GRID"):
        candidates.append({"id": f"{feature_id}:{category}:{x:.3f}:{y:.3f}", "source_id":feature_id,"category":category,"position":[round(x,3),round(-y,3)],"yaw_rad":round(yaw,8),"grounding":grounding,"placement_rule":rule,"confidence":.35,"base_surface":context.base(Point(x,y))})

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
            add_surface(props["id"], "PAVING_BORDER", geom.difference(geom.buffer(-POLICY['paving_width'])), "INFERRED")
        if tags.get("crossing") == "zebra" and geom.geom_type in ("Polygon", "MultiPolygon"):
            add_surface(props["id"], "ZEBRA_CROSSING", geom, "VERIFIED_GEOGRAPHIC")

    for feature in features("bgc-open-spaces.geojson"):
        props = feature["properties"]
        if props["id"] not in PARK_IDS:
            continue
        geom = shape(feature["geometry"])
        owners[props["id"]] = geom
        add_surface(props["id"], "PARK_EDGE", geom.difference(geom.buffer(-POLICY['park_edge_width'])), "INFERRED")
        # Repeated grid is stable and sparse. It represents landscaped character only.
        xmin, ymin, xmax, ymax = geom.bounds
        grid = POLICY["tree_grid"]
        for gx in range(math.floor(xmin / grid), math.ceil(xmax / grid) + 1):
            for gy in range(math.floor(ymin / grid), math.ceil(ymax / grid) + 1):
                seed = f"{props['id']}:{gx}:{gy}".encode()
                digest = hashlib.sha256(seed).digest()
                x = gx * grid + (digest[0] / 255 - .5) * POLICY['tree_grid_jitter']
                y = gy * grid + (digest[1] / 255 - .5) * POLICY['tree_grid_jitter']
                point = Point(x, y)
                if not geom.buffer(-POLICY['park_inset']).covers(point):
                    continue
                if digest[2] < 115:
                    add_instance(props["id"], "TREE_CLUSTER", x, y, "INFERRED", digest[3]/255*math.tau)
                elif digest[2] < 150:
                    add_instance(props["id"], "PLANTER_RECT", x, y, "INFERRED", boundary_frame(geom, geom.exterior.project(point), 0)[1])

    # Sample selected High Street polygon boundaries. Each point stays near mapped
    # pedestrian space; exact furniture locations are deliberately marked inferred.
    for feature in paths:
        props = feature["properties"]
        if props.get("name") != "Bonifacio High Street":
            continue
        geom = shape(feature["geometry"])
        if geom.geom_type != "Polygon" or geom.area < 100 or not geom.intersects(CORE):
            continue
        owners[props["id"]] = geom
        boundary = geom.exterior
        interval = POLICY["boundary_interval"]
        for i in range(1, min(int(boundary.length // interval), 20)):
            point = boundary.interpolate(i * interval)
            if not CORE.covers(point):
                continue
            category = ("BENCH_LINEAR", "LIGHT_POLE_STANDARD", "PLANTER_RECT")[i % 3]
            frame = boundary_frame(geom, i * interval, POLICY['inset'][category])
            if frame:
                point,yaw = frame
                add_instance(props["id"], category, point.x, point.y, "INFERRED", 0 if category == "LIGHT_POLE_STANDARD" else yaw, "BOUNDARY_INSET")

    accepted = []
    for candidate in sorted(candidates, key=lambda c:c['id']):
        stat = stats.setdefault(candidate['category'], Counter())
        stat['candidates'] += 1
        reason = context.rejection(candidate, owners[candidate['source_id']], accepted)
        if reason:
            stat['rejected_'+reason] += 1
            continue
        accepted.append(candidate)
        stat['accepted'] += 1
        for tile_id, extent in tiles:
            if extent.covers(Point(candidate['position'][0],-candidate['position'][1])):
                tile_record(tile_id)['instances'].setdefault(candidate['category'],[]).append(candidate)
                break
    package['statistics'] = stats
    package['exclusion_inputs'] = context.counts
    # Deduplicate source entries and provide compact counts for reproducible QA.
    for item in package["tiles"].values():
        item["sources"] = list({(s["id"], s["category"], s["grounding"]): s for s in item["sources"]}.values())
    inputs = sorted(list(PROCESSED.glob('bgc-*.geojson')) + list((ROOT/'web/public/world/tiles').glob('*.json')) + [ROOT/'data/config/surface-heights.json'])
    package['input_sha256'] = {str(path.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs}
    package["counts"] = {
        "tiles": len(package["tiles"]),
        "surfaces": sum(sum(len(v) for v in t["surfaces"].values()) for t in package["tiles"].values()),
        "instances": sum(sum(len(v) for v in t["instances"].values()) for t in package["tiles"].values()),
    }
    (ROOT / "web/components/runtime/surface-heights.generated.json").write_text(json.dumps(HEIGHTS,sort_keys=True)+"\n")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(package, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}: {package['counts']}")


if __name__ == "__main__":
    main()
