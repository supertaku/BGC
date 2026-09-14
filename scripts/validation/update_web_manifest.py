"""Copy the validated pilot GLB to the viewer and refresh manifest asset metrics."""

from __future__ import annotations

import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[2]
GLB = ROOT / "exports" / "glb" / "bgc-pilot-base.glb"
METRICS = ROOT / "exports" / "glb" / "bgc-pilot-base.metrics.json"
VIEWER_GLB = ROOT / "web" / "public" / "models" / "bgc-pilot-base.glb"
MANIFEST = ROOT / "web" / "public" / "world" / "pilot-world.json"
REGISTRY = ROOT / "data" / "assets" / "buildings.json"


def main() -> None:
    metrics = json.loads(METRICS.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    approved = [
        entry for entry in registry["buildings"].values()
        if entry.get("available_lods", {}).get("1", {}).get("status") == "APPROVED"
    ]
    if metrics.get("validation") != "PASS":
        raise RuntimeError("Refusing to publish an unvalidated GLB")
    VIEWER_GLB.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(GLB, VIEWER_GLB)
    manifest["asset"].update({
        "url": "/models/bgc-pilot-base.glb",
        "size_bytes": metrics["file_size_bytes"],
        "triangles": metrics["triangle_count"],
        "meshes": metrics["mesh_count"],
        "materials": metrics["material_count"],
    })
    manifest["asset"]["central_square_lod"] = "LOD1"
    manifest["asset"]["w_global_center_lod"] = "LOD1"
    manifest["asset"]["reconstructed_lod1_entities"] = [entry["entity_id"] for entry in approved]
    building_views = [
        {"id": "central-square", "label": "Central Square", "position": [-248, 20, -275], "target": [-268, 11, -122]},
        {"id": "central-square-street", "label": "Central Square Street", "position": [-289, 8, 30], "target": [-268, 11, -122]},
        {"id": "w-global-near", "label": "W Global Center", "position": [35, 20, -112], "target": [98, 14, -40]},
        {"id": "w-global-street", "label": "W Global Center Street", "position": [104, 12, -150], "target": [104, 14, -52]},
    ]
    fixed_ids = {item["id"] for item in building_views}
    for entry in approved:
        if entry["entity_id"] in {"bgc_building_0014", "bgc_building_0007"}:
            continue
        entity = json.loads((ROOT / "data" / "reconstruction_packages" / entry["entity_id"] / "entity.json").read_text(encoding="utf-8"))
        cx = float(entity["centroid"].get("local_x_m", entity["centroid"].get("x")))
        cy = float(entity["centroid"].get("local_y_m", entity["centroid"].get("y")))
        height = float(entity["height"]["value_m"])
        view_id = entry["entity_id"].replace("bgc_building_", "building-")
        building_views.append({
            "id": view_id,
            "label": entry["name"],
            "position": [round(cx + max(55, height * 0.65), 3), round(max(16, height * 0.45), 3), round(-cy + max(55, height * 0.65), 3)],
            "target": [round(cx, 3), round(height * 0.38, 3), round(-cy, 3)],
        })
        fixed_ids.add(view_id)
    building_view_ids = {item["id"] for item in building_views}
    manifest["viewpoints"] = [
        viewpoint for viewpoint in manifest["viewpoints"]
        if viewpoint.get("id") not in building_view_ids
    ]
    manifest["viewpoints"].extend(building_views)
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"BGC_WEB_ASSET: copied={VIEWER_GLB.relative_to(ROOT)} bytes={VIEWER_GLB.stat().st_size}")


if __name__ == "__main__":
    main()
