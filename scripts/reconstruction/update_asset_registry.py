"""Create runtime manifests from validated building metrics and verify identity links."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "data" / "assets" / "buildings.json"


def validate_asset_path(root: Path, lod: dict, metrics: dict) -> None:
    asset_path = root / lod["asset"]
    if not asset_path.is_file() or asset_path.stat().st_size != metrics["file_size_bytes"]:
        raise ValueError("ASSET_REGISTRY_ERROR: asset path or byte count does not match metrics")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entity_id")
    parser.add_argument("--lod", type=int, default=1)
    args = parser.parse_args()
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    try:
        entry = registry["buildings"][args.entity_id]
        lod = entry["available_lods"][str(args.lod)]
    except KeyError as exc:
        raise SystemExit(f"ASSET_REGISTRY_ERROR: missing {exc.args[0]!r} for {args.entity_id} LOD{args.lod}") from exc
    metrics_path = ROOT / lod["metrics"]
    asset_path = ROOT / lod["asset"]
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    if metrics.get("validation") != "PASS":
        raise SystemExit("ASSET_REGISTRY_ERROR: metrics are not validated")
    if metrics.get("entity_id") != entry["entity_id"] or entry["entity_id"] != args.entity_id:
        raise SystemExit("METADATA_ERROR: registry, metrics, and requested entity IDs differ")
    try:
        validate_asset_path(ROOT, lod, metrics)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    entity = json.loads((ROOT / "data" / "reconstruction_packages" / args.entity_id / "entity.json").read_text(encoding="utf-8"))
    if entity.get("entity_id") != args.entity_id:
        raise SystemExit("METADATA_ERROR: canonical package entity ID differs")
    manifest = {
        "schema_version": "1.0",
        "entity_id": args.entity_id,
        "name": entry["name"],
        "lod": args.lod,
        "asset": lod["asset"],
        "bounds_m": metrics["bounds_m"],
        "geographic_anchor": entity["centroid"],
        "evidence_status": entry["lifecycle"]["evidence"],
        "metrics": lod["metrics"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runtime_metadata_policy": "compact identity/component IDs in GLB extras; canonical evidence external",
    }
    output = ROOT / lod["manifest"]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"ASSET_REGISTRY: PASS manifest={output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
