"""Fetch an immutable BGC snapshot from the official OSM map API in cells.

The adapter emits the Overpass-style JSON geometry consumed by normalize_osm.py.
It is a bounded fallback for public Overpass timeouts, not a second data model.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from fetch_osm import boundary_bbox, file_sha256, find_cached


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "data" / "raw" / "osm"
ENDPOINT = "https://api.openstreetmap.org/api/0.6/map"


def element_metadata(xml_element: ET.Element) -> dict:
    result = {"type": xml_element.tag, "id": int(xml_element.attrib["id"])}
    for source, target, cast in (("version", "version", int), ("changeset", "changeset", int), ("timestamp", "timestamp", str), ("user", "user", str), ("uid", "uid", int)):
        if source in xml_element.attrib:
            result[target] = cast(xml_element.attrib[source])
    tags = {tag.attrib["k"]: tag.attrib["v"] for tag in xml_element.findall("tag")}
    if tags:
        result["tags"] = tags
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--boundary", type=Path, required=True)
    parser.add_argument("--label", default="bgc")
    parser.add_argument("--grid", type=int, default=4)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    if args.grid < 1 or args.grid > 10:
        raise ValueError("--grid must be between 1 and 10")
    boundary = args.boundary.resolve()
    bbox = boundary_bbox(boundary)
    south, west, north, east = bbox
    boxes = []
    for row in range(args.grid):
        for column in range(args.grid):
            boxes.append((
                west + (east - west) * column / args.grid,
                south + (north - south) * row / args.grid,
                west + (east - west) * (column + 1) / args.grid,
                south + (north - south) * (row + 1) / args.grid,
            ))
    urls = [f"{ENDPOINT}?bbox={west:.7f},{south:.7f},{east:.7f},{north:.7f}" for west, south, east, north in boxes]
    boundary_hash = file_sha256(boundary)
    query_hash = hashlib.sha256("\n".join(urls).encode("utf-8")).hexdigest()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cached = find_cached(args.label, boundary_hash, query_hash)
    if cached and not args.refresh:
        print(f"BGC_OSM_MAP: using cached {cached[0].relative_to(ROOT)}")
        return

    nodes: dict[int, dict] = {}
    ways: dict[int, dict] = {}
    relations: dict[int, dict] = {}
    for index, url in enumerate(urls, start=1):
        request = Request(url, headers={"User-Agent": "BGC3DTour/0.3 whole-city-ingestion"})
        with urlopen(request, timeout=180) as response:
            root = ET.fromstring(response.read())
        for xml_node in root.findall("node"):
            node = element_metadata(xml_node)
            node.update({"lat": float(xml_node.attrib["lat"]), "lon": float(xml_node.attrib["lon"])})
            nodes[node["id"]] = node
        for xml_way in root.findall("way"):
            way = element_metadata(xml_way)
            way["nodes"] = [int(nd.attrib["ref"]) for nd in xml_way.findall("nd")]
            ways[way["id"]] = way
        for xml_relation in root.findall("relation"):
            relation = element_metadata(xml_relation)
            relation["members"] = [
                {"type": member.attrib["type"], "ref": int(member.attrib["ref"]), "role": member.attrib.get("role", "")}
                for member in xml_relation.findall("member")
            ]
            relations[relation["id"]] = relation
        print(f"BGC_OSM_MAP: cell={index}/{len(urls)} nodes={len(nodes)} ways={len(ways)} relations={len(relations)}", flush=True)

    for way in ways.values():
        way["geometry"] = [
            {"lat": nodes[node_id]["lat"], "lon": nodes[node_id]["lon"]}
            for node_id in way["nodes"] if node_id in nodes
        ]
    for relation in relations.values():
        for member in relation["members"]:
            if member["type"] == "way" and member["ref"] in ways:
                member["geometry"] = ways[member["ref"]].get("geometry", [])

    retained_nodes = [node for node in nodes.values() if node.get("tags")]
    payload = {
        "version": 0.6,
        "generator": "openstreetmap-map-api-grid-adapter",
        "elements": sorted([*retained_nodes, *ways.values(), *relations.values()], key=lambda item: (item["type"], item["id"])),
    }
    body = (json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
    acquired = datetime.now(timezone.utc)
    timestamp = acquired.strftime("%Y-%m-%dT%H%M%SZ")
    raw_path = OUTPUT_DIR / f"{args.label}-{timestamp}.json"
    meta_path = OUTPUT_DIR / f"{args.label}-{timestamp}.meta.json"
    raw_path.write_bytes(body)
    raw_hash = hashlib.sha256(body).hexdigest()
    metadata = {
        "schema_version": 1,
        "source_id": "source:osm",
        "source_title": "OpenStreetMap official map API",
        "source_url": ENDPOINT,
        "license": "ODbL 1.0",
        "attribution": "© OpenStreetMap contributors",
        "retrieved_at": acquired.isoformat(),
        "boundary_path": str(boundary.relative_to(ROOT)).replace("\\", "/"),
        "boundary_sha256": boundary_hash,
        "bbox_south_west_north_east": list(bbox),
        "query": "\n".join(urls),
        "query_sha256": query_hash,
        "query_profile": "whole-city-map-api-grid",
        "query_grid": args.grid,
        "sha256": raw_hash,
        "element_count": len(payload["elements"]),
        "raw_path": str(raw_path.relative_to(ROOT)).replace("\\", "/"),
    }
    meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"BGC_OSM_MAP: fetched elements={len(payload['elements'])} snapshot={raw_path.name} sha256={raw_hash[:12]}")


if __name__ == "__main__":
    main()
