"""Minimal Blender CLI/bpy integration test."""

from pathlib import Path
import sys
import traceback

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from scene_tools import (
    add_camera,
    add_daylight,
    clear_scene,
    configure_scene,
    create_building,
    create_material,
    create_road,
    create_sidewalk,
    render_png,
    save_blend,
)


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    clear_scene()
    configure_scene()
    ground = create_material("Ground", (0.16, 0.28, 0.18, 1.0))
    road = create_material("Road", (0.055, 0.065, 0.08, 1.0), roughness=0.9)
    sidewalk = create_material("Sidewalk", (0.48, 0.5, 0.52, 1.0))
    warm = create_material("BuildingWarm", (0.62, 0.27, 0.16, 1.0))
    cool = create_material("BuildingCool", (0.12, 0.3, 0.48, 1.0), roughness=0.55)

    from scene_tools import create_box
    create_box("Ground", (0, 0, -0.16), (80, 60, 0.3), ground)
    create_road("Road", 0, 0, 12, 80, "x", road)
    create_sidewalk("SidewalkNorth", 0, 7.5, 3, 80, "x", sidewalk)
    create_sidewalk("SidewalkSouth", 0, -7.5, 3, 80, "x", sidewalk)
    create_building("BuildingA", -24, 18, 16, 14, 18, warm)
    create_building("BuildingB", 0, 19, 18, 16, 28, cool)
    create_building("BuildingC", 25, 17, 14, 18, 22, warm)
    add_daylight()
    add_camera("IntegrationCamera", (68, -70, 58), (0, 6, 10), lens=52)

    save_blend(ROOT / "blender" / "scenes" / "integration-test.blend")
    render_png(ROOT / "blender" / "renders" / "integration-test.png")
    print("BGC_PIPELINE: integration test complete")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
