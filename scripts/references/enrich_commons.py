"""Stage B: rights-enrich only shortlisted Commons candidates in small batches."""

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
from evidence.model import normalize_name, read_json, review_rights, stable_hash, write_json  # noqa: E402

DISCOVERY_PATH = ROOT / "data" / "references" / "commons-discovery.json"
ENTITIES_PATH = ROOT / "data" / "entities" / "pilot-entities.json"
CACHE_DIR = ROOT / "data" / "cache" / "commons" / "enrichment"
OUTPUT_PATH = ROOT / "data" / "references" / "references-unreviewed.json"
RIGHTS_REVIEW_PATH = ROOT / "data" / "review" / "rights-review.json"
REFERENCE_REVIEW_PATH = ROOT / "data" / "review" / "reference-review.json"
API_URL = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "BGC3DTour/0.5 (rights-reviewed reference enrichment; contact via repository maintainers)"
EXT_FIELDS = "LicenseShortName|LicenseUrl|Artist|Credit|DateTimeOriginal|DateTime|ImageDescription|ObjectName|UsageTerms|AttributionRequired"


def plain(value: str | None) -> str | None:
    if not value:
        return None
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html.unescape(value))).strip() or None


def request_json(params: dict[str, str], attempts: int = 5) -> dict:
    url = f"{API_URL}?{urlencode(params)}"
    for attempt in range(attempts):
        try:
            with urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=60) as response:
                return json.load(response)
        except (HTTPError, URLError, TimeoutError) as exc:
            if attempt + 1 == attempts:
                raise RuntimeError(f"Commons enrichment failed: {exc}") from exc
            retry_after = int(exc.headers.get("Retry-After", "0")) if isinstance(exc, HTTPError) and exc.headers else 0
            time.sleep(max(retry_after, 2 ** attempt, 2))
    raise AssertionError("unreachable")


def meta(metadata: dict, key: str) -> str | None:
    return plain(metadata.get(key, {}).get("value"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--batch-size", type=int, default=20)
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 50:
        raise SystemExit("--batch-size must be between 1 and 50")
    discovery = read_json(DISCOVERY_PATH)
    entities = {entity["entity_id"]: entity for entity in read_json(ENTITIES_PATH)["entities"]}
    shortlisted = [item for item in discovery.get("candidates", []) if item["discovery_status"] == "SHORTLISTED"]
    pageids = sorted({item["source_item_id"] for item in shortlisted})
    pages: dict[str, dict] = {}
    request_count = 0
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    for start in range(0, len(pageids), args.batch_size):
        batch = pageids[start:start + args.batch_size]
        key = stable_hash(batch)[:16]
        cache_path = CACHE_DIR / f"batch-{key}.json"
        if cache_path.is_file() and not args.refresh:
            response = read_json(cache_path)
        else:
            response = request_json({
                "action": "query", "format": "json", "formatversion": "2",
                "pageids": "|".join(batch), "prop": "imageinfo|coordinates|categories",
                "iiprop": "url|size|mime|sha1|timestamp|user|extmetadata", "iiurlwidth": "640",
                "iiextmetadatafilter": EXT_FIELDS, "iiextmetadatalanguage": "en",
                "cllimit": "20",
            })
            write_json(cache_path, response)
            request_count += 1
            time.sleep(1.0)
        for page in response.get("query", {}).get("pages", []):
            pages[str(page["pageid"])] = page

    now = datetime.now(timezone.utc).isoformat()
    records = []
    rights_reviews = []
    reference_reviews = []
    for candidate in shortlisted:
        page = pages.get(candidate["source_item_id"])
        if not page:
            reference_reviews.append({"candidate_id": candidate["candidate_id"], "reason": "enrichment_missing", "recommended_action": "RETRY"})
            continue
        info = (page.get("imageinfo") or [{}])[0]
        metadata = info.get("extmetadata", {})
        license_name = meta(metadata, "LicenseShortName")
        license_url = meta(metadata, "LicenseUrl")
        creator = meta(metadata, "Artist") or info.get("user")
        rights = review_rights(license_name, license_url, creator)
        entity = entities[candidate["entity_id"]]
        title_normalized = normalize_name(page.get("title")) or ""
        name_normalized = entity.get("normalized_name") or ""
        exact_title = bool(name_normalized and name_normalized in title_normalized)
        mime = info.get("mime")
        title_has_bgc = "bonifacio global city" in title_normalized or "bgc" in title_normalized
        accepted = exact_title and entity["identity_status"] == "CONFIRMED" and bool(mime and mime.startswith("image/")) and title_has_bgc
        match_status = "ACCEPTED" if accepted else "REVIEW_REQUIRED"
        coordinate = (page.get("coordinates") or [{}])[0]
        record = {
            "reference_id": f"ref:commons:{page['pageid']}",
            "source_id": "source:wikimedia-commons",
            "source_item_id": str(page["pageid"]),
            "entity_links": [{"entity_id": candidate["entity_id"], "relationship": "FACADE" if accepted else "UNKNOWN", "confidence": 0.95 if accepted else 0.55}],
            "source_page_url": info.get("descriptionurl") or f"https://commons.wikimedia.org/wiki/{page.get('title','').replace(' ', '_')}",
            "asset_url": info.get("url"),
            "thumbnail_url": info.get("thumburl"),
            "title": page.get("title"),
            "creator": creator,
            "capture_date": meta(metadata, "DateTimeOriginal"),
            "upload_date": info.get("timestamp"),
            "latitude": coordinate.get("lat"),
            "longitude": coordinate.get("lon"),
            "view_direction": None,
            "viewpoint_side": None,
            "viewpoint_side_status": "UNKNOWN",
            "facade_depicted": "UNKNOWN",
            "source_hash": info.get("sha1"),
            "mime_type": mime,
            "width": info.get("width"),
            "height": info.get("height"),
            "license_id": license_name,
            "license_url": license_url,
            "credit_line": meta(metadata, "Credit") or creator,
            **rights,
            "rights_reviewed_at": now if rights["rights_status"] == "REUSE_CAPABLE" else None,
            "local_file_path": None,
            "storage_status": "REMOTE_METADATA_ONLY",
            "reference_role": "FACADE" if accepted else "UNKNOWN",
            "entity_match_status": match_status,
            "decision_method": "MULTI_SIGNAL_AUTOMATIC" if accepted else "SOL_REVIEW",
            "decision_timestamp": now,
            "confidence": 0.95 if accepted else 0.55,
            "supporting_evidence": ["Exact canonical name tokens in title", "BGC location tokens in title", f"Entity identity is {entity['identity_status']}"] if accepted else ["Title match requires human confirmation or entity identity is not confirmed"],
            "categories": [item.get("title") for item in page.get("categories", [])],
        }
        records.append(record)
        if rights["rights_status"] == "REVIEW_REQUIRED":
            rights_reviews.append({"reference_id": record["reference_id"], "license": license_name, "creator": creator, "reason": rights["rights_notes"], "recommended_action": "REVIEW_RIGHTS"})
        if match_status == "REVIEW_REQUIRED":
            reference_reviews.append({"reference_id": record["reference_id"], "entity_id": candidate["entity_id"], "title": page.get("title"), "evidence": record["supporting_evidence"], "recommended_action": "REVIEW_ENTITY_MATCH"})

    write_json(OUTPUT_PATH, {"schema_version": 1, "generated_at": now, "stage": "RIGHTS_ENRICHMENT", "network_requests": request_count, "full_resolution_downloads": 0, "records": records})
    write_json(RIGHTS_REVIEW_PATH, {"schema_version": 1, "generated_at": now, "items": rights_reviews})
    write_json(REFERENCE_REVIEW_PATH, {"schema_version": 1, "generated_at": now, "items": reference_reviews})
    print(f"BGC_COMMONS_ENRICH: shortlisted={len(shortlisted)} enriched={len(records)} accepted={sum(r['entity_match_status']=='ACCEPTED' for r in records)} rights_review={len(rights_reviews)} requests={request_count} downloads=0")


if __name__ == "__main__":
    main()
