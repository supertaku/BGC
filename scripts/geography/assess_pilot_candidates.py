"""Measure comparable OSM and Wikimedia coverage for proposed pilot zones."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from geo_utils import local_xy


ROOT = Path(__file__).resolve().parents[2]
CANDIDATES_PATH = ROOT / "data" / "geographic" / "pilot-candidates.json"
OUTPUT_PATH = ROOT / "data" / "processed" / "pilot-candidate-assessment.json"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
COMMONS_URL = "https://commons.wikimedia.org/w/api.php"


def request_json(url: str, params: dict[str, str], method: str = "GET") -> dict:
    encoded = urlencode(params)
    if method == "POST":
        request = Request(url, data=encoded.encode("utf-8"), method="POST")
    else:
        request = Request(f"{url}?{encoded}")
    request.add_header("User-Agent", "BGC3DTour/0.1 pilot-candidate-assessment")
    with urlopen(request, timeout=90) as response:
        return json.load(response)


def fetch_osm_elements(bbox: list[float]) -> list[dict]:
    south, west, north, east = bbox
    bbox_text = f"{south},{west},{north},{east}"
    query = f"""[out:json][timeout:60];
(
  nwr[\"building\"]({bbox_text});
  nwr[\"highway\"]({bbox_text});
  nwr[\"leisure\"]({bbox_text});
  nwr[\"natural\"]({bbox_text});
  nwr[\"amenity\"]({bbox_text});
  nwr[\"shop\"]({bbox_text});
);
out tags center;"""
    return request_json(OVERPASS_URL, {"data": query}, method="POST").get("elements", [])


def element_point(element: dict) -> tuple[float, float] | None:
    if "lat" in element and "lon" in element:
        return float(element["lat"]), float(element["lon"])
    center = element.get("center")
    if center:
        return float(center["lat"]), float(center["lon"])
    return None


def osm_metrics(all_elements: list[dict], bbox: list[float]) -> dict:
    south, west, north, east = bbox
    elements = []
    for element in all_elements:
        point = element_point(element)
        if point and south <= point[0] <= north and west <= point[1] <= east:
            elements.append(element)
    building_elements = [element for element in elements if "building" in element.get("tags", {})]
    highway_elements = [element for element in elements if "highway" in element.get("tags", {})]
    pedestrian_values = {"footway", "pedestrian", "path", "steps", "living_street"}
    furniture_amenities = {"bench", "waste_basket", "drinking_water", "bicycle_parking"}
    unique = {(element["type"], element["id"]): element for element in elements}
    return {
        "unique_elements": len(unique),
        "buildings": len(building_elements),
        "named_buildings": sum(bool(element.get("tags", {}).get("name")) for element in building_elements),
        "buildings_with_height": sum("height" in element.get("tags", {}) for element in building_elements),
        "buildings_with_levels": sum("building:levels" in element.get("tags", {}) for element in building_elements),
        "highways": len(highway_elements),
        "pedestrian_ways": sum(element.get("tags", {}).get("highway") in pedestrian_values for element in highway_elements),
        "open_space_features": sum(
            element.get("tags", {}).get("leisure") in {"park", "garden", "playground", "pitch"}
            or element.get("tags", {}).get("landuse") in {"grass", "recreation_ground"}
            for element in elements
        ),
        "vegetation_features": sum(
            element.get("tags", {}).get("natural") in {"tree", "tree_row", "wood", "scrub"}
            for element in elements
        ),
        "street_furniture_features": sum(
            element.get("tags", {}).get("amenity") in furniture_amenities
            or element.get("tags", {}).get("highway") == "street_lamp"
            for element in elements
        ),
        "shops": sum("shop" in element.get("tags", {}) for element in elements),
        "amenities": sum("amenity" in element.get("tags", {}) for element in elements),
    }


def commons_metrics(bbox: list[float]) -> dict:
    south, west, north, east = bbox
    center_lat = (south + north) / 2
    center_lon = (west + east) / 2
    west_south = local_xy(west, south, (center_lon, center_lat))
    east_north = local_xy(east, north, (center_lon, center_lat))
    radius = min(10000, int(max(abs(west_south[0]), abs(west_south[1]), abs(east_north[0]), abs(east_north[1])) * 1.15))
    payload = request_json(COMMONS_URL, {
        "action": "query",
        "format": "json",
        "list": "geosearch",
        "gscoord": f"{center_lat}|{center_lon}",
        "gsradius": str(radius),
        "gslimit": "500",
        "gsnamespace": "6",
    })
    results = payload.get("query", {}).get("geosearch", [])
    return {
        "geotagged_files": len(results),
        "search_radius_m": radius,
        "sample_titles": [result["title"] for result in results[:8]],
        "caveat": "Geosearch measures nearby geotagged Commons files, not facade coverage or license suitability. Each file still requires metadata review."
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if OUTPUT_PATH.is_file() and not args.force:
        print(f"BGC_CANDIDATES: using cached {OUTPUT_PATH.relative_to(ROOT)}")
        return

    input_payload = json.loads(CANDIDATES_PATH.read_text(encoding="utf-8"))
    boxes = [candidate["bbox"] for candidate in input_payload["candidates"]]
    union_bbox = [
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    ]
    all_osm_elements = fetch_osm_elements(union_bbox)
    results = []
    for candidate in input_payload["candidates"]:
        south, west, north, east = candidate["bbox"]
        center = ((west + east) / 2, (south + north) / 2)
        corners = [
            local_xy(longitude, latitude, center)
            for longitude, latitude in ((west, south), (east, south), (east, north), (west, north))
        ]
        result = dict(candidate)
        result["approximate_width_m"] = round(max(x for x, _ in corners) - min(x for x, _ in corners), 1)
        result["approximate_depth_m"] = round(max(y for _, y in corners) - min(y for _, y in corners), 1)
        result["osm"] = osm_metrics(all_osm_elements, candidate["bbox"])
        result["wikimedia_commons"] = commons_metrics(candidate["bbox"])
        result["mapillary"] = {
            "coverage": "not measured",
            "reason": "Mapillary Graph API access requires a project token; assess interactively or with a configured token before reference acquisition."
        }
        results.append(result)
        print(f"BGC_CANDIDATES: assessed {candidate['id']}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps({
        "schema_version": 1,
        "assessed_at": datetime.now(timezone.utc).isoformat(),
        "sources": ["source:osm", "source:wikimedia-commons"],
        "candidates": results
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"BGC_CANDIDATES: wrote {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
