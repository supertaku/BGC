"""Cache a bounded, target-specific Wikimedia Commons evidence search.

This script downloads metadata only. It combines a small set of name queries,
two relevant Commons categories, and a 300 m geosearch around Central Square.
Media files are deliberately not downloaded.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import html
import json
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from evidence.model import read_json, stable_hash, write_json  # noqa: E402


API_URL = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "BGC3DTour/0.6 (target evidence research; contact via repository maintainers)"
CACHE_DIR = ROOT / "data" / "cache" / "commons" / "m6-central-square"
OUTPUT_PATH = ROOT / "data" / "references" / "central-square-commons-discovery.json"
TARGET = {"latitude": 14.5519147, "longitude": 121.0484706, "radius_m": 300}

SEARCHES = [
    '"Central Square" "Bonifacio Global City"',
    '"Central Square" BGC',
    '"Bonifacio High Street" "30th Street"',
    '"Bonifacio High Street" "5th Avenue"',
]

CATEGORIES = [
    "Category:Bonifacio High Street",
    "Category:Buildings in Bonifacio Global City",
]

EXT_FIELDS = (
    "LicenseShortName|LicenseUrl|Artist|Credit|DateTimeOriginal|DateTime|"
    "ImageDescription|ObjectName|UsageTerms|AttributionRequired"
)


def request_json(params: dict[str, str], *, refresh: bool, label: str) -> tuple[dict, bool]:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"{label}-{stable_hash(params)[:16]}.json"
    if cache_path.is_file() and not refresh:
        return read_json(cache_path), False
    url = f"{API_URL}?{urlencode(params)}"
    for attempt in range(5):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(request, timeout=60) as response:
                payload = json.load(response)
            write_json(cache_path, payload)
            return payload, True
        except (HTTPError, URLError, TimeoutError) as exc:
            if attempt == 4:
                raise RuntimeError(f"Commons request failed for {label}: {exc}") from exc
            retry_after = int(exc.headers.get("Retry-After", "0")) if isinstance(exc, HTTPError) and exc.headers else 0
            time.sleep(max(retry_after, 2**attempt, 2))
    raise AssertionError("unreachable")


def page_ids_from_search(payload: dict) -> list[str]:
    return [str(item["pageid"]) for item in payload.get("query", {}).get("search", [])]


def page_ids_from_category(payload: dict) -> list[str]:
    return [str(item["pageid"]) for item in payload.get("query", {}).get("categorymembers", [])]


def page_ids_from_geosearch(payload: dict) -> list[str]:
    return [str(item["pageid"]) for item in payload.get("query", {}).get("geosearch", [])]


def plain(value: str | None) -> str | None:
    if not value:
        return None
    text = re.sub(r"<[^>]+>", "", html.unescape(value))
    return re.sub(r"\s+", " ", text).strip() or None


def metadata_value(metadata: dict, key: str) -> str | None:
    return plain((metadata.get(key) or {}).get("value"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Refresh cached API responses")
    args = parser.parse_args()

    discovered: dict[str, set[str]] = {}
    request_count = 0

    for index, query in enumerate(SEARCHES, start=1):
        payload, requested = request_json(
            {
                "action": "query",
                "format": "json",
                "formatversion": "2",
                "list": "search",
                "srnamespace": "6",
                "srsearch": query,
                "srlimit": "20",
                "srprop": "timestamp",
            },
            refresh=args.refresh,
            label=f"search-{index}",
        )
        request_count += int(requested)
        for page_id in page_ids_from_search(payload):
            discovered.setdefault(page_id, set()).add(f"SEARCH:{query}")
        if requested:
            time.sleep(1)

    for index, category in enumerate(CATEGORIES, start=1):
        payload, requested = request_json(
            {
                "action": "query",
                "format": "json",
                "formatversion": "2",
                "list": "categorymembers",
                "cmtitle": category,
                "cmnamespace": "6",
                "cmtype": "file",
                "cmlimit": "100",
            },
            refresh=args.refresh,
            label=f"category-{index}",
        )
        request_count += int(requested)
        for page_id in page_ids_from_category(payload):
            discovered.setdefault(page_id, set()).add(f"CATEGORY:{category}")
        if requested:
            time.sleep(1)

    payload, requested = request_json(
        {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "list": "geosearch",
            "gsnamespace": "6",
            "gscoord": f"{TARGET['latitude']}|{TARGET['longitude']}",
            "gsradius": str(TARGET["radius_m"]),
            "gslimit": "100",
        },
        refresh=args.refresh,
        label="geosearch",
    )
    request_count += int(requested)
    for page_id in page_ids_from_geosearch(payload):
        discovered.setdefault(page_id, set()).add("GEOSEARCH:300m")

    pages: dict[str, dict] = {}
    page_ids = sorted(discovered, key=int)
    for batch_index, start in enumerate(range(0, len(page_ids), 50), start=1):
        batch = page_ids[start : start + 50]
        payload, requested = request_json(
            {
                "action": "query",
                "format": "json",
                "formatversion": "2",
                "pageids": "|".join(batch),
                "prop": "imageinfo|coordinates|categories",
                "iiprop": "url|size|mime|sha1|timestamp|user|extmetadata|commonmetadata",
                "iiurlwidth": "960",
                "iiextmetadatafilter": EXT_FIELDS,
                "iiextmetadatalanguage": "en",
                "cllimit": "50",
            },
            refresh=args.refresh,
            label=f"enrichment-{batch_index}",
        )
        request_count += int(requested)
        for page in payload.get("query", {}).get("pages", []):
            pages[str(page["pageid"])] = page
        if requested:
            time.sleep(1)

    records = []
    for page_id in page_ids:
        page = pages.get(page_id, {"pageid": int(page_id)})
        info = (page.get("imageinfo") or [{}])[0]
        coordinate = (page.get("coordinates") or [{}])[0]
        metadata = info.get("extmetadata", {})
        records.append(
            {
                "page_id": page_id,
                "title": page.get("title"),
                "discovery_channels": sorted(discovered[page_id]),
                "source_page_url": info.get("descriptionurl"),
                "asset_url": info.get("url"),
                "thumbnail_url": info.get("thumburl"),
                "width": info.get("width"),
                "height": info.get("height"),
                "mime_type": info.get("mime"),
                "source_hash": info.get("sha1"),
                "upload_date": info.get("timestamp"),
                "latitude": coordinate.get("lat"),
                "longitude": coordinate.get("lon"),
                "capture_date_raw": metadata_value(metadata, "DateTimeOriginal")
                or metadata_value(metadata, "DateTime"),
                "creator": metadata_value(metadata, "Artist") or info.get("user"),
                "credit_line": metadata_value(metadata, "Credit"),
                "license_id": metadata_value(metadata, "LicenseShortName"),
                "license_url": metadata_value(metadata, "LicenseUrl"),
                "usage_terms": metadata_value(metadata, "UsageTerms"),
                "description": metadata_value(metadata, "ImageDescription")
                or metadata_value(metadata, "ObjectName"),
                "categories": [item.get("title") for item in page.get("categories", [])],
            }
        )

    generated_at = datetime.now(timezone.utc).isoformat()
    write_json(
        OUTPUT_PATH,
        {
            "schema_version": 1,
            "generated_at": generated_at,
            "stage": "M6_TARGET_SPECIFIC_DISCOVERY",
            "target": TARGET,
            "queries": SEARCHES,
            "categories": CATEGORIES,
            "network_requests": request_count,
            "full_resolution_downloads": 0,
            "records": records,
        },
    )
    print(
        "BGC_M6_COMMONS: "
        f"candidates={len(records)} requests={request_count} downloads=0 output={OUTPUT_PATH.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
