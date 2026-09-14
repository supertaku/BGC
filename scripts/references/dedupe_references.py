"""Deduplicate enriched references without losing multi-entity links."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from evidence.model import dedupe_reference_records, read_json, write_json  # noqa: E402

INPUT_PATH = ROOT / "data" / "references" / "references-unreviewed.json"
OFFICIAL_PATH = ROOT / "data" / "references" / "official-research-references.json"
OUTPUT_PATH = ROOT / "data" / "references" / "references.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=INPUT_PATH)
    parser.add_argument("--additional", type=Path, default=OFFICIAL_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    payload = read_json(args.input)
    if payload is None:
        raise RuntimeError(f"Missing input: {args.input}")
    input_records = list(payload.get("records", []))
    additional = read_json(args.additional, {}) or {}
    input_records.extend(additional.get("records", []))
    records, duplicates = dedupe_reference_records(input_records)
    write_json(args.output, {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dedupe_precedence": ["source-native item ID", "canonical source URL", "source SHA1"],
        "input_records": len(input_records),
        "duplicates_removed": duplicates,
        "records": records,
    })
    print(f"BGC_REFERENCE_DEDUPE: input={len(input_records)} output={len(records)} duplicates={duplicates}")


if __name__ == "__main__":
    main()
