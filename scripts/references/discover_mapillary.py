"""Mapillary integration boundary; metadata-only and credentials-safe."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
BOUNDARY_PATH = ROOT / "data" / "geographic" / "pilot-boundary.geojson"
OUTPUT_PATH = ROOT / "references" / "metadata" / "mapillary-pilot.json"
API_URL = "https://graph.mapillary.com/images"


def bbox() -> list[float]:
    payload = json.loads(BOUNDARY_PATH.read_text(encoding="utf-8"))
    ring = payload["features"][0]["geometry"]["coordinates"][0]
    return [min(point[0] for point in ring), min(point[1] for point in ring), max(point[0] for point in ring), max(point[1] for point in ring)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    if OUTPUT_PATH.is_file() and not args.refresh:
        print(f"BGC_MAPILLARY: using cached {OUTPUT_PATH.relative_to(ROOT)}")
        return
    token = os.environ.get("MAPILLARY_ACCESS_TOKEN")
    retrieved_at = datetime.now(timezone.utc).isoformat()
    base = {
        "schema_version": 1,
        "source": "source:mapillary",
        "api": API_URL,
        "retrieved_at": retrieved_at,
        "discovery_only": True,
        "downloaded_images": 0,
        "bbox_west_south_east_north": bbox(),
        "requested_fields": ["id", "geometry", "computed_geometry", "captured_at", "compass_angle", "computed_compass_angle", "sequence", "creator", "is_pano"],
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not token:
        base.update({
            "status": "BLOCKED_CREDENTIALS",
            "records": [],
            "requirement": "Set MAPILLARY_ACCESS_TOKEN to a valid Mapillary client token, then run with --refresh.",
            "notes": "Credential absence does not block geographic normalization, Blender generation, GLB export, or the viewer.",
        })
        OUTPUT_PATH.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
        print("BGC_MAPILLARY: BLOCKED_CREDENTIALS (integration boundary written; no fabricated token)")
        return

    fields = ",".join(base["requested_fields"])
    request = Request(f"{API_URL}?{urlencode({'bbox': ','.join(map(str, base['bbox_west_south_east_north'])), 'limit': str(min(max(args.limit, 1), 50)), 'fields': fields})}")
    request.add_header("Authorization", f"OAuth {token}")
    request.add_header("User-Agent", "BGC3DTour/0.2 reference-discovery-poc")
    with urlopen(request, timeout=90) as response:
        payload = json.load(response)
    base.update({"status": "PASS", "records": payload.get("data", [])})
    OUTPUT_PATH.write_text(json.dumps(base, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"BGC_MAPILLARY: records={len(base['records'])} downloads=0")


if __name__ == "__main__":
    main()
