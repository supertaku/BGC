"""Check generated detail ownership, source traceability and determinism."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from shapely.geometry import Point, Polygon, box

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "web/components/runtime/visual-detail.json"


def main():
    before = hashlib.sha256(PACKAGE.read_bytes()).hexdigest()
    subprocess.run([sys.executable, str(ROOT / "scripts/visual_detail/build_visual_detail.py")], cwd=ROOT, check=True)
    after = hashlib.sha256(PACKAGE.read_bytes()).hexdigest()
    if before != after:
        raise AssertionError("Visual-detail build is not deterministic")
    detail = json.loads(PACKAGE.read_text(encoding="utf-8"))
    world = json.loads((ROOT / "web/public/world/bgc-world.json").read_text(encoding="utf-8"))
    bounds = {tile["tile_id"]: box(*tile["bounds"]) for tile in world["tiles"]}
    for tile_id, record in detail["tiles"].items():
        extent = bounds[tile_id]
        sources = {source["id"] for source in record["sources"]}
        for polygons in record["surfaces"].values():
            for item in polygons:
                polygon = Polygon(item["outer"], item["holes"])
                if polygon.is_empty or not polygon.is_valid or not extent.buffer(.02).covers(polygon):
                    raise AssertionError(f"Invalid/out-of-tile surface: {tile_id}")
        for instances in record["instances"].values():
            for item in instances:
                x, z = item["position"]
                if not extent.buffer(.02).covers(Point(x, -z)):
                    raise AssertionError(f"Invalid/out-of-tile instance: {tile_id}/{item['id']}")
                if not any(item["id"].startswith(source + ":") for source in sources):
                    raise AssertionError(f"Missing instance provenance: {item['id']}")
    print(f"Visual detail verified: {detail['counts']}, SHA256 {after}")


if __name__ == "__main__":
    main()
