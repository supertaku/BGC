"""Prove structured polygon data can generate Blender geometry."""

import json
from pathlib import Path
import sys
import traceback

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from scene_tools import clear_scene, configure_scene, create_footprint_building, create_material, save_blend


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    source = ROOT / "data" / "entities" / "synthetic-buildings.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    clear_scene()
    configure_scene()
    materials = {
        "warm": create_material("StructuredWarm", (0.55, 0.24, 0.13, 1.0)),
        "blue": create_material("StructuredBlue", (0.1, 0.29, 0.5, 1.0)),
        "neutral": create_material("StructuredNeutral", (0.48, 0.46, 0.42, 1.0)),
    }
    for record in payload["buildings"]:
        obj = create_footprint_building(record["id"], record["footprint"], float(record["height"]), materials[record["material"]])
        obj["source_id"] = record["id"]
        obj["source_file"] = source.name
    save_blend(ROOT / "blender" / "scenes" / "structured-data-test.blend")
    print(f"BGC_PIPELINE: generated {len(payload['buildings'])} buildings from {source.name}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
