"""Publish generated M11 tiles and viewer/registry manifests."""

from __future__ import annotations

import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[2]
SOURCE_MANIFEST = ROOT / "exports" / "bgc" / "manifest.json"
PUBLIC_MODELS = ROOT / "web" / "public" / "models"
PUBLIC_WORLD = ROOT / "web" / "public" / "world" / "bgc-world.json"
REGISTRY_PATH = ROOT / "data" / "assets" / "buildings.json"


def main() -> None:
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    incomplete = [tile["tile_id"] for tile in manifest["tiles"] if tile.get("status") != "PASS"]
    if incomplete:
        raise RuntimeError(f"Cannot publish incomplete M11 tiles: {incomplete}")
    tile_target = PUBLIC_MODELS / "bgc" / "tiles"
    building_target = PUBLIC_MODELS / "buildings"
    tile_target.mkdir(parents=True, exist_ok=True)
    building_target.mkdir(parents=True, exist_ok=True)
    for tile in manifest["tiles"]:
        source = ROOT / "exports" / "bgc" / tile["asset_path"]
        shutil.copy2(source, tile_target / source.name)

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    detailed_assets = []
    for entry in registry.get("buildings", {}).values():
        lod1 = entry.get("available_lods", {}).get("1")
        if not lod1 or lod1.get("status") != "APPROVED":
            continue
        source = ROOT / lod1["asset"]
        if not source.is_file():
            raise FileNotFoundError(f"Approved LOD1 asset missing: {source}")
        target = building_target / source.name
        shutil.copy2(source, target)
        detailed_assets.append({"entity_id": entry["entity_id"], "name": entry.get("name"), "url": f"/models/buildings/{source.name}", "lod": "LOD1"})
        source_ids = set(entry.get("source_feature_ids", []))
        owning_tiles = sorted(tile["tile_id"] for tile in manifest["tiles"] if source_ids.intersection(tile.get("entities", [])))
        entry.setdefault("available_lods", {})["2"] = {
            "representation": "WHOLE_BGC_TILE",
            "manifest": "exports/bgc/manifest.json",
            "owning_tiles": owning_tiles,
            "source_feature_ids": sorted(source_ids),
            "generator": "blender/scripts/generate_bgc_tiles.py",
            "version": str(manifest["pipeline_version"]),
            "status": "AVAILABLE",
        }
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    bounds = manifest["boundary"]["bounds"]
    center_x, center_y = (bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2
    extent = max(bounds[2] - bounds[0], bounds[3] - bounds[1])
    world = {
        "world_id": manifest["world_id"],
        "title": "Whole-BGC low-fidelity skeleton",
        "tiles": [
            {"tile_id": tile["tile_id"], "url": f"/models/bgc/tiles/{tile['tile_id']}.glb", "center": tile["center"], "bounds": tile["bounds"], "size_bytes": tile["bytes"], "triangles": tile["triangle_count"], "meshes": tile["mesh_count"]}
            for tile in manifest["tiles"]
        ],
        "detailed_assets": detailed_assets,
        "totals": manifest["totals"],
        "tile_loading": manifest["tile_loading"],
        "viewpoints": [
            {"id": "bgc-aerial-full", "label": "BGC Aerial Full", "position": [center_x + extent * 0.72, extent * 0.88, -(center_y - extent * 0.72)], "target": [center_x, 24, -center_y]},
            {"id": "bgc-high-street", "label": "BGC High Street", "position": [-90, 16, 170], "target": [-120, 12, 10]},
            {"id": "bgc-north", "label": "BGC North", "position": [center_x, extent * 0.48, -(bounds[3] + extent * 0.42)], "target": [center_x, 20, -center_y]},
            {"id": "bgc-south", "label": "BGC South", "position": [center_x, extent * 0.48, -(bounds[1] - extent * 0.42)], "target": [center_x, 20, -center_y]},
            {"id": "bgc-south-street", "label": "South Street", "position": [300, 7, 800], "target": [180, 8, 650]},
        ],
        "attribution": {"text": "© OpenStreetMap contributors", "url": "https://www.openstreetmap.org/copyright", "license": "ODbL 1.0", "license_url": "https://opendatacommons.org/licenses/odbl/1-0/"},
    }
    PUBLIC_WORLD.parent.mkdir(parents=True, exist_ok=True)
    PUBLIC_WORLD.write_text(json.dumps(world, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"BGC_PUBLISH: tiles={len(world['tiles'])} lod1={len(detailed_assets)} bytes={manifest['totals']['glb_bytes']}")


if __name__ == "__main__":
    main()
