"""Stage A: bounded, metadata-cheap Commons discovery for named pilot entities."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from evidence.model import normalize_name, read_json, stable_hash, write_json  # noqa: E402

ENTITIES_PATH = ROOT / "data" / "entities" / "pilot-entities.json"
CACHE_DIR = ROOT / "data" / "cache" / "commons" / "discovery"
OUTPUT_PATH = ROOT / "data" / "references" / "commons-discovery.json"
API_URL = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "BGC3DTour/0.5 (rights-reviewed reference discovery; contact via repository maintainers)"
GENERIC_NAMES = {"c1", "c2", "c3", "b 1", "b 2", "b 3", "b 5", "b 8", "bench", "maybank", "uniqlo", "live street"}


def request_json(params: dict[str, str], attempts: int = 5) -> dict:
    url = f"{API_URL}?{urlencode(params)}"
    for attempt in range(attempts):
        try:
            with urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=60) as response:
                return json.load(response)
        except (HTTPError, URLError, TimeoutError) as exc:
            if attempt + 1 == attempts:
                raise RuntimeError(f"Commons discovery failed: {exc}") from exc
            retry_after = int(exc.headers.get("Retry-After", "0")) if isinstance(exc, HTTPError) and exc.headers else 0
            time.sleep(max(retry_after, 2 ** attempt, 2))
    raise AssertionError("unreachable")


def title_matches(name: str, title: str) -> bool:
    wanted = [token for token in (normalize_name(name) or "").split() if len(token) > 1]
    present = set((normalize_name(title) or "").split())
    return bool(wanted) and all(token in present for token in wanted)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--limit-per-entity", type=int, default=3)
    parser.add_argument("--max-entities", type=int, default=12)
    args = parser.parse_args()
    if not 1 <= args.limit_per_entity <= 10:
        raise SystemExit("--limit-per-entity must be between 1 and 10")
    entities = read_json(ENTITIES_PATH)["entities"]
    targets = [
        entity for entity in entities
        if entity.get("canonical_name")
        and entity["identity_status"] in {"CONFIRMED", "HIGH_CONFIDENCE", "REVIEW_REQUIRED"}
        and entity.get("normalized_name") not in GENERIC_NAMES
    ][: max(1, args.max_entities)]
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    candidates = []
    request_count = 0
    for entity in targets:
        query = f'"{entity["canonical_name"]}" "Bonifacio Global City"'
        key = stable_hash({"query": query, "limit": args.limit_per_entity})[:16]
        cache_path = CACHE_DIR / f"{entity['entity_id']}-{key}.json"
        if cache_path.is_file() and not args.refresh:
            response = read_json(cache_path)
        else:
            response = request_json({
                "action": "query", "format": "json", "formatversion": "2",
                "list": "search", "srnamespace": "6", "srsearch": query,
                "srlimit": str(args.limit_per_entity), "srprop": "timestamp",
            })
            write_json(cache_path, response)
            request_count += 1
            time.sleep(1.0)
        for item in response.get("query", {}).get("search", []):
            title = item.get("title", "")
            candidates.append({
                "candidate_id": f"commons:{item['pageid']}:{entity['entity_id']}",
                "source_item_id": str(item["pageid"]),
                "title": title,
                "entity_id": entity["entity_id"],
                "query": query,
                "discovery_status": "SHORTLISTED" if title_matches(entity["canonical_name"], title) else "REJECTED",
                "match_signals": {
                    "exact_name_tokens_in_title": title_matches(entity["canonical_name"], title),
                    "entity_identity_status": entity["identity_status"],
                },
                "rejection_reason": None if title_matches(entity["canonical_name"], title) else "title_name_mismatch",
            })
    write_json(OUTPUT_PATH, {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "api": API_URL,
        "stage": "CHEAP_DISCOVERY",
        "targets": len(targets),
        "candidate_cap_per_entity": args.limit_per_entity,
        "network_requests": request_count,
        "full_resolution_downloads": 0,
        "candidates": candidates,
    })
    print(f"BGC_COMMONS_DISCOVERY: targets={len(targets)} candidates={len(candidates)} shortlisted={sum(c['discovery_status']=='SHORTLISTED' for c in candidates)} requests={request_count} downloads=0")


if __name__ == "__main__":
    main()
