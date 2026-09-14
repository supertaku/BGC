"""Batch-enrich directly linked Wikidata entities with cached API responses."""

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
from evidence.model import read_json, write_json  # noqa: E402

ENTITIES_PATH = ROOT / "data" / "entities" / "pilot-entities.json"
CACHE_DIR = ROOT / "data" / "cache" / "wikidata"
OUTPUT_PATH = ROOT / "data" / "entities" / "wikidata-enrichment.json"
API_URL = "https://www.wikidata.org/w/api.php"
USER_AGENT = "BGC3DTour/0.5 (reference intelligence; contact via repository maintainers)"

PROPERTY_MAP = {
    "P18": "image",
    "P31": "instance_of",
    "P127": "owner",
    "P137": "operator",
    "P571": "inception",
    "P625": "coordinates",
    "P856": "official_website",
    "P1101": "number_of_floors",
    "P1619": "official_opening_date",
    "P2048": "height",
    "P373": "commons_category",
}


def request_json(params: dict[str, str], attempts: int = 3) -> dict:
    url = f"{API_URL}?{urlencode(params)}"
    for attempt in range(attempts):
        try:
            with urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=60) as response:
                return json.load(response)
        except (HTTPError, URLError, TimeoutError) as exc:
            if attempt + 1 == attempts:
                raise RuntimeError(f"Wikidata request failed after {attempts} attempts: {exc}") from exc
            time.sleep(2 ** attempt)
    raise AssertionError("unreachable")


def claim_value(claim: dict) -> object:
    value = claim.get("mainsnak", {}).get("datavalue", {}).get("value")
    if isinstance(value, dict):
        if "amount" in value:
            amount = value["amount"]
            try:
                return float(amount)
            except (TypeError, ValueError):
                return amount
        if "latitude" in value and "longitude" in value:
            return {"latitude": value["latitude"], "longitude": value["longitude"], "precision": value.get("precision")}
        if "id" in value:
            return value["id"]
        if "time" in value:
            return value["time"]
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Refetch even when a matching cache file exists.")
    args = parser.parse_args()
    entities = read_json(ENTITIES_PATH)
    qids = sorted({entity["wikidata_id"] for entity in entities["entities"] if entity.get("wikidata_id")})
    if not qids:
        write_json(OUTPUT_PATH, {"schema_version": 1, "retrieved_at": None, "entities": {}})
        print("BGC_WIKIDATA: qids=0")
        return
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / ("entities-" + "-".join(qids) + ".json")
    if cache_path.is_file() and not args.refresh:
        raw = read_json(cache_path)
        cache_status = "cached"
    else:
        raw = request_json({
            "action": "wbgetentities",
            "format": "json",
            "formatversion": "2",
            "ids": "|".join(qids),
            "props": "labels|aliases|descriptions|claims|sitelinks",
            "languages": "en",
            "sitefilter": "enwiki",
        })
        write_json(cache_path, raw)
        cache_status = "refreshed"
    normalized = {}
    for qid, entity in raw.get("entities", {}).items():
        claims = entity.get("claims", {})
        normalized[qid] = {
            "label": entity.get("labels", {}).get("en", {}).get("value"),
            "aliases": [item["value"] for item in entity.get("aliases", {}).get("en", [])],
            "description": entity.get("descriptions", {}).get("en", {}).get("value"),
            "wikipedia_title": entity.get("sitelinks", {}).get("enwiki", {}).get("title"),
            "properties": {
                label: [claim_value(claim) for claim in claims.get(pid, []) if claim.get("rank") != "deprecated"]
                for pid, label in PROPERTY_MAP.items()
                if claims.get(pid)
            },
            "source_url": f"https://www.wikidata.org/wiki/{qid}",
        }
    write_json(OUTPUT_PATH, {
        "schema_version": 1,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "api": API_URL,
        "cache_file": str(cache_path.relative_to(ROOT)).replace("\\", "/"),
        "entities": normalized,
    })
    print(f"BGC_WIKIDATA: qids={len(qids)} mode={cache_status}")


if __name__ == "__main__":
    main()

