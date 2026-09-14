"""Small, metadata-only Wikimedia Commons discovery proof of concept."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import html
import json
from pathlib import Path
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
BUILDINGS_PATH = ROOT / "data" / "processed" / "pilot-buildings.geojson"
BOUNDARY_PATH = ROOT / "data" / "geographic" / "pilot-boundary.geojson"
OUTPUT_PATH = ROOT / "references" / "metadata" / "wikimedia-pilot.json"
COVERAGE_PATH = ROOT / "references" / "metadata" / "pilot-reference-coverage.json"
API_URL = "https://commons.wikimedia.org/w/api.php"
TARGET_NAMES = ("Central Square", "JY Campos Center", "W Global Center")
EXT_FIELDS = (
    "LicenseShortName|LicenseUrl|Artist|Credit|DateTimeOriginal|ImageDescription|"
    "ObjectName|UsageTerms"
)


def plain(value: str | None) -> str | None:
    if not value:
        return None
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html.unescape(value))).strip() or None


def request_json(params: dict[str, str]) -> dict:
    request = Request(f"{API_URL}?{urlencode(params)}", headers={"User-Agent": "BGC3DTour/0.2 reference-discovery-poc"})
    with urlopen(request, timeout=90) as response:
        return json.load(response)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--limit-per-building", type=int, default=2)
    args = parser.parse_args()
    if OUTPUT_PATH.is_file() and COVERAGE_PATH.is_file() and not args.refresh:
        print(f"BGC_COMMONS: using cached {OUTPUT_PATH.relative_to(ROOT)}")
        return
    buildings = json.loads(BUILDINGS_PATH.read_text(encoding="utf-8"))["features"]
    boundary_ring = json.loads(BOUNDARY_PATH.read_text(encoding="utf-8"))["features"][0]["geometry"]["coordinates"][0]
    west, east = min(point[0] for point in boundary_ring), max(point[0] for point in boundary_ring)
    south, north = min(point[1] for point in boundary_ring), max(point[1] for point in boundary_ring)
    by_name = {feature["properties"].get("name"): feature for feature in buildings}
    missing = [name for name in TARGET_NAMES if name not in by_name]
    if missing:
        raise RuntimeError(f"Reference targets are absent from normalized buildings: {missing}")

    retrieved_at = datetime.now(timezone.utc).isoformat()
    records = []
    coverage = []
    for name in TARGET_NAMES:
        entity_id = by_name[name]["properties"]["id"]
        response = request_json({
            "action": "query", "format": "json", "formatversion": "2",
            "generator": "search", "gsrsearch": f"{name} Bonifacio Global City Philippines", "gsrnamespace": "6",
            "gsrlimit": str(max(1, min(args.limit_per_building, 5))),
            "prop": "imageinfo|coordinates",
            "iiprop": "url|timestamp|user|extmetadata", "iiurlwidth": "640",
            "iiextmetadatafilter": EXT_FIELDS, "iiextmetadatalanguage": "en",
        })
        target_refs = []
        for page in response.get("query", {}).get("pages", []):
            info = (page.get("imageinfo") or [{}])[0]
            metadata = info.get("extmetadata", {})
            coordinate = (page.get("coordinates") or [{}])[0]
            reference_id = f"ref:commons:{page['pageid']}"
            latitude = coordinate.get("lat")
            longitude = coordinate.get("lon")
            title_words = set(re.findall(r"[a-z0-9]+", (page.get("title") or "").lower()))
            name_words = {word for word in re.findall(r"[a-z0-9]+", name.lower()) if len(word) > 1}
            rejection_reason = None
            if latitude is not None and longitude is not None and not (west - 0.01 <= longitude <= east + 0.01 and south - 0.01 <= latitude <= north + 0.01):
                rejection_reason = "geographically_outside_pilot"
            elif not name_words.issubset(title_words):
                rejection_reason = "title_name_mismatch"
            status = "REJECTED" if rejection_reason else "DISCOVERY_CANDIDATE"
            if status == "DISCOVERY_CANDIDATE":
                target_refs.append(reference_id)
            records.append({
                "reference_id": reference_id,
                "source": "source:wikimedia-commons",
                "source_url": info.get("descriptionurl"),
                "source_item_id": str(page["pageid"]),
                "title": page.get("title"),
                "entity_id": entity_id,
                "entity_match_status": status,
                "entity_match_method": "building_name_search; manual identity review required",
                "entity_match_confidence": 0.25,
                "rejection_reason": rejection_reason,
                "image_url": info.get("url"),
                "thumbnail_url": info.get("thumburl"),
                "creator": plain(metadata.get("Artist", {}).get("value")),
                "capture_date": plain(metadata.get("DateTimeOriginal", {}).get("value")),
                "latitude": latitude,
                "longitude": longitude,
                "direction": None,
                "license": plain(metadata.get("LicenseShortName", {}).get("value")),
                "license_url": plain(metadata.get("LicenseUrl", {}).get("value")),
                "attribution": plain(metadata.get("Credit", {}).get("value")),
                "retrieval_date": retrieved_at,
                "storage_status": "REMOTE_METADATA_ONLY",
                "redistribution_status": "REQUIRES_PER_FILE_REVIEW",
                "notes": "Search result only. No local image was downloaded and no facade orientation was inferred.",
            })
        coverage.append({
            "entity_id": entity_id,
            "entity_name": name,
            "orientation_status": "UNKNOWN",
            "discovery_candidates": len(target_refs),
            "candidate_reference_ids": target_refs,
            "aspects": {
                "north_facade": {"rating": "NONE", "accepted_references": []},
                "south_facade": {"rating": "NONE", "accepted_references": []},
                "east_facade": {"rating": "NONE", "accepted_references": []},
                "west_facade": {"rating": "NONE", "accepted_references": []},
                "entrance": {"rating": "NONE", "accepted_references": []},
                "roof": {"rating": "NONE", "accepted_references": []},
                "street_context": {"rating": "UNASSESSED", "candidate_references": target_refs},
            },
        })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps({
        "schema_version": 1,
        "source": "source:wikimedia-commons",
        "api": API_URL,
        "retrieved_at": retrieved_at,
        "discovery_only": True,
        "downloaded_images": 0,
        "records": records,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    COVERAGE_PATH.write_text(json.dumps({
        "schema_version": 1,
        "generated_at": retrieved_at,
        "method": "metadata-only Commons proof of concept; candidates are not accepted evidence",
        "buildings": coverage,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"BGC_COMMONS: targets={len(TARGET_NAMES)} candidates={len(records)} downloads=0")


if __name__ == "__main__":
    main()
