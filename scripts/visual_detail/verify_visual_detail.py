"""Check generated detail ownership, source traceability and determinism."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from shapely.geometry import Point, Polygon, box, shape
from placement import Context, HEIGHTS, load_features
import math

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "web/public/world/detail/high-street-public-realm.json"


def main():
    before = hashlib.sha256(PACKAGE.read_bytes()).hexdigest()
    subprocess.run([sys.executable, str(ROOT / "scripts/visual_detail/build_visual_detail.py")], cwd=ROOT, check=True)
    after = hashlib.sha256(PACKAGE.read_bytes()).hexdigest()
    if before != after:
        raise AssertionError("Visual-detail build is not deterministic")
    detail = json.loads(PACKAGE.read_text(encoding="utf-8"))
    world = json.loads((ROOT / "web/public/world/bgc-world.json").read_text(encoding="utf-8"))
    bounds = {tile["tile_id"]: box(*tile["bounds"]) for tile in world["tiles"]}
    assert json.loads((ROOT / "web/components/runtime/surface-heights.generated.json").read_text()) == HEIGHTS
    context=Context()
    owners={f["properties"]["id"]:shape(f["geometry"]) for f in load_features("paths")+load_features("open-spaces")}
    accepted=[]
    ids=set()
    assert detail["schema_version"] == 2
    for tile_id, record in detail["tiles"].items():
        extent = bounds[tile_id]
        sources = {source["id"] for source in record["sources"]}
        for polygons in record["surfaces"].values():
            for item in polygons:
                assert all(item.get(k) for k in ('id','source_id','category','grounding','base_surface'))
                assert item['source_id'] in owners
                assert item['id'] not in ids
                ids.add(item['id'])
                assert item['base_surface']+'_TOP' in HEIGHTS
                assert 0 < item['elevation_offset_m'] <= .02
                assert all(math.isfinite(v) for ring in [item['outer']]+item['holes'] for pair in ring for v in pair)
                polygon = Polygon(item["outer"], item["holes"])
                for base, mask in [('PATH',context.path),('OPEN_SPACE',context.open),('ROAD',context.road)]:
                    if HEIGHTS[base+'_TOP'] > HEIGHTS[item['base_surface']+'_TOP']:
                        assert polygon.intersection(mask.buffer(-.02)).area < .01, ('buried',item['id'])
                if polygon.is_empty or not polygon.is_valid or not extent.buffer(.02).covers(polygon):
                    raise AssertionError(f"Invalid/out-of-tile surface: {tile_id}")
        for instances in record["instances"].values():
            for item in instances:
                assert all(item.get(k) for k in ('id','source_id','category','grounding','base_surface','placement_rule'))
                assert math.isfinite(item['yaw_rad']) and all(map(math.isfinite,item['position']))
                assert item['id'] not in ids
                ids.add(item['id'])
                assert context.rejection(item,owners[item['source_id']],accepted) is None, item['id']
                accepted.append(item)
                x, z = item["position"]
                if not extent.buffer(.02).covers(Point(x, -z)):
                    raise AssertionError(f"Invalid/out-of-tile instance: {tile_id}/{item['id']}")
                if item["source_id"] not in owners:
                    raise AssertionError(f"Missing instance provenance: {item['id']}")
    print(f"Visual detail verified: {detail['counts']}, SHA256 {after}")


if __name__ == "__main__":
    main()
