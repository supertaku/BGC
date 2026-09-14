"""Fetch immutable, metadata-rich Overpass snapshots for an arbitrary boundary."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BOUNDARY = ROOT / "data" / "geographic" / "pilot-boundary.geojson"
OUTPUT_DIR = ROOT / "data" / "raw" / "osm"
DEFAULT_ENDPOINT = "https://overpass-api.de/api/interpreter"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def boundary_bbox(path: Path) -> tuple[float, float, float, float]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    coordinates = payload["features"][0]["geometry"]["coordinates"]

    def points(value):
        if value and isinstance(value[0], (int, float)):
            yield value
        else:
            for child in value:
                yield from points(child)

    pairs = list(points(coordinates))
    longitudes = [float(pair[0]) for pair in pairs]
    latitudes = [float(pair[1]) for pair in pairs]
    return min(latitudes), min(longitudes), max(latitudes), max(longitudes)


def build_query(bbox: tuple[float, float, float, float], profile: str = "pilot") -> str:
    south, west, north, east = bbox
    box = f"{south:.7f},{west:.7f},{north:.7f},{east:.7f}"
    if profile == "whole-city":
        # M11 intentionally excludes POI/street-furniture nodes. Keeping the
        # response to massing and district context makes the boundary-wide
        # immutable snapshot practical on public Overpass infrastructure.
        return f'''[out:json][timeout:240];
(
  wr["building"]({box});
  wr["building:part"]({box});
  way["highway"]({box});
  wr["leisure"~"^(park|garden|playground|pitch|recreation_ground)$"]({box});
  wr["landuse"~"^(grass|recreation_ground|village_green|forest|meadow)$"]({box});
  wr["natural"~"^(wood|scrub|grassland|water)$"]({box});
);
out meta geom;'''
    return f'''[out:json][timeout:120];
(
  nwr["building"]({box});
  nwr["building:part"]({box});
  nwr["highway"]({box});
  nwr["leisure"]({box});
  nwr["amenity"]({box});
  nwr["natural"]({box});
  nwr["barrier"]({box});
  nwr["landuse"]({box});
);
out meta geom;'''


def find_cached(label: str, boundary_hash: str, query_hash: str) -> tuple[Path, Path] | None:
    for meta_path in sorted(OUTPUT_DIR.glob(f"{label}-*.meta.json"), reverse=True):
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        raw_path = meta_path.with_name(meta_path.name.replace(".meta.json", ".json"))
        if (
            raw_path.is_file()
            and metadata.get("boundary_sha256") == boundary_hash
            and metadata.get("query_sha256") == query_hash
            and metadata.get("sha256") == file_sha256(raw_path)
        ):
            return raw_path, meta_path
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--boundary", type=Path, default=DEFAULT_BOUNDARY)
    parser.add_argument("--label", default="pilot")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--profile", choices=("pilot", "whole-city"), default="pilot")
    parser.add_argument("--grid", type=int, default=1, help="split the bbox into an N x N query grid and deduplicate elements")
    parser.add_argument("--refresh", action="store_true", help="acquire a new immutable snapshot")
    args = parser.parse_args()

    boundary = args.boundary.resolve()
    if not boundary.is_file():
        raise FileNotFoundError(boundary)
    bbox = boundary_bbox(boundary)
    if args.grid < 1 or args.grid > 10:
        raise ValueError("--grid must be between 1 and 10")
    south, west, north, east = bbox
    queries = []
    for row in range(args.grid):
        for column in range(args.grid):
            cell = (
                south + (north - south) * row / args.grid,
                west + (east - west) * column / args.grid,
                south + (north - south) * (row + 1) / args.grid,
                west + (east - west) * (column + 1) / args.grid,
            )
            queries.append(build_query(cell, args.profile))
    query = "\n\n".join(queries)
    boundary_hash = file_sha256(boundary)
    query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cached = find_cached(args.label, boundary_hash, query_hash)
    if cached and not args.refresh:
        print(f"BGC_OSM: using cached {cached[0].relative_to(ROOT)}")
        return

    elements_by_id = {}
    generator = None
    for index, cell_query in enumerate(queries, start=1):
        request = Request(
            args.endpoint,
            data=urlencode({"data": cell_query}).encode("utf-8"),
            headers={"User-Agent": "BGC3DTour/0.2 grounded-pilot-ingestion"},
            method="POST",
        )
        with urlopen(request, timeout=180) as response:
            parsed_cell = json.loads(response.read())
        if not isinstance(parsed_cell.get("elements"), list):
            raise RuntimeError(f"Overpass response {index}/{len(queries)} has no elements array")
        generator = generator or parsed_cell.get("generator")
        for element in parsed_cell["elements"]:
            elements_by_id[(element.get("type"), element.get("id"))] = element
        print(f"BGC_OSM: cell={index}/{len(queries)} elements={len(parsed_cell['elements'])} unique={len(elements_by_id)}", flush=True)
    parsed = {
        "version": 0.6,
        "generator": generator or "combined-overpass-grid",
        "elements": [elements_by_id[key] for key in sorted(elements_by_id, key=lambda item: (str(item[0]), int(item[1])))],
    }
    if not parsed["elements"]:
        raise RuntimeError("Overpass returned an empty whole-boundary dataset; refusing to cache it")
    body = (json.dumps(parsed, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")

    acquired = datetime.now(timezone.utc)
    timestamp = acquired.strftime("%Y-%m-%dT%H%M%SZ")
    raw_path = OUTPUT_DIR / f"{args.label}-{timestamp}.json"
    meta_path = OUTPUT_DIR / f"{args.label}-{timestamp}.meta.json"
    if raw_path.exists() or meta_path.exists():
        raise FileExistsError(f"Refusing to overwrite snapshot timestamp {timestamp}")
    raw_path.write_bytes(body)
    raw_hash = hashlib.sha256(body).hexdigest()
    metadata = {
        "schema_version": 1,
        "source_id": "source:osm",
        "source_title": "OpenStreetMap via Overpass API",
        "source_url": args.endpoint,
        "license": "ODbL 1.0",
        "attribution": "© OpenStreetMap contributors",
        "retrieved_at": acquired.isoformat(),
        "boundary_path": str(boundary.relative_to(ROOT)).replace("\\", "/"),
        "boundary_sha256": boundary_hash,
        "bbox_south_west_north_east": list(bbox),
        "query": query,
        "query_profile": args.profile,
        "query_grid": args.grid,
        "query_sha256": query_hash,
        "sha256": raw_hash,
        "element_count": len(parsed["elements"]),
        "raw_path": str(raw_path.relative_to(ROOT)).replace("\\", "/"),
    }
    meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"BGC_OSM: fetched elements={len(parsed['elements'])} snapshot={raw_path.name} sha256={raw_hash[:12]}")


if __name__ == "__main__":
    main()
