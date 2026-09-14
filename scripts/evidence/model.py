"""Small, dependency-free rules shared by M5 entity/reference tools."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any


EVIDENCE_STRENGTH = {
    "UNKNOWN": 0,
    "PROCEDURAL": 1,
    "INFERRED": 2,
    "ESTIMATED": 3,
    "VERIFIED_PHOTOGRAPHIC": 4,
    "VERIFIED_GEOGRAPHIC": 5,
    "VERIFIED_STRUCTURED": 6,
    "VERIFIED_AUTHORITATIVE": 7,
}

KNOWN_REUSE_LICENSES = {
    "cc0": (False, False),
    "public domain": (False, False),
    "pd": (False, False),
    "cc by 2.0": (True, False),
    "cc by 3.0": (True, False),
    "cc by 4.0": (True, False),
    "cc by-sa 2.0": (True, True),
    "cc by-sa 3.0": (True, True),
    "cc by-sa 4.0": (True, True),
}


def normalize_name(value: str | None) -> str | None:
    if not value:
        return None
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    tokens = re.findall(r"[a-z0-9]+", ascii_value.lower())
    return " ".join(tokens) or None


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def read_json(path: Path, default: Any = None) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def review_rights(license_name: str | None, license_url: str | None, creator: str | None) -> dict[str, Any]:
    """Conservative file-level rights normalization; never upgrades unknown terms."""
    normalized = normalize_name(license_name)
    recognized = None
    if normalized:
        for key, requirements in KNOWN_REUSE_LICENSES.items():
            if normalize_name(key) == normalized:
                recognized = requirements
                break
    if recognized is None:
        return {
            "rights_status": "REVIEW_REQUIRED",
            "viewable_for_research": True,
            "local_copy_allowed": None,
            "derivative_use_allowed": None,
            "commercial_use_allowed": None,
            "redistribution_allowed": None,
            "attribution_required": None,
            "share_alike_required": None,
            "rights_notes": "License is missing or not in the reviewed allow-list.",
        }
    attribution_required, share_alike_required = recognized
    if attribution_required and not creator:
        return {
            "rights_status": "REVIEW_REQUIRED",
            "viewable_for_research": True,
            "local_copy_allowed": None,
            "derivative_use_allowed": None,
            "commercial_use_allowed": None,
            "redistribution_allowed": None,
            "attribution_required": True,
            "share_alike_required": share_alike_required,
            "rights_notes": "Recognized license but creator/credit metadata is missing.",
        }
    return {
        "rights_status": "REUSE_CAPABLE",
        "viewable_for_research": True,
        "local_copy_allowed": True,
        "derivative_use_allowed": True,
        "commercial_use_allowed": True,
        "redistribution_allowed": True,
        "attribution_required": attribution_required,
        "share_alike_required": share_alike_required,
        "rights_notes": "Automated normalization of explicit Commons metadata; release still requires attribution assembly.",
    }


def resolve_observations(observations: list[dict[str, Any]]) -> dict[str, Any]:
    """Select strongest evidence while retaining ties/conflicts."""
    if not observations:
        return {"selected": None, "conflicted": False, "candidates": []}
    ranked = sorted(
        observations,
        key=lambda item: (EVIDENCE_STRENGTH.get(item.get("status", "UNKNOWN"), -1), item.get("confidence", 0)),
        reverse=True,
    )
    strongest = EVIDENCE_STRENGTH.get(ranked[0].get("status", "UNKNOWN"), -1)
    peers = [item for item in ranked if EVIDENCE_STRENGTH.get(item.get("status", "UNKNOWN"), -1) == strongest]
    values = {json.dumps(item.get("value"), sort_keys=True) for item in peers}
    return {"selected": ranked[0], "conflicted": len(values) > 1, "candidates": ranked}


def coverage_rating(reference_ids: list[str], *, accepted: bool = True) -> str:
    if not reference_ids:
        return "NONE"
    if not accepted:
        return "WEAK"
    return "PARTIAL" if len(set(reference_ids)) == 1 else "GOOD"


def dedupe_reference_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Deduplicate by source ID, canonical page URL, then source hash; preserve links."""
    output: list[dict[str, Any]] = []
    indexes: dict[tuple[str, str], int] = {}
    duplicates = 0
    for record in records:
        keys = []
        if record.get("source_item_id"):
            keys.append(("source_item_id", f"{record.get('source_id')}:{record['source_item_id']}"))
        if record.get("source_page_url"):
            keys.append(("source_page_url", record["source_page_url"].rstrip("/")))
        if record.get("source_hash"):
            keys.append(("source_hash", record["source_hash"]))
        existing_index = next((indexes[key] for key in keys if key in indexes), None)
        if existing_index is None:
            existing_index = len(output)
            output.append(json.loads(json.dumps(record)))
            for key in keys:
                indexes[key] = existing_index
            continue
        duplicates += 1
        existing = output[existing_index]
        links = existing.setdefault("entity_links", [])
        for link in record.get("entity_links", []):
            if link not in links:
                links.append(link)
        for key in keys:
            indexes[key] = existing_index
    return output, duplicates
