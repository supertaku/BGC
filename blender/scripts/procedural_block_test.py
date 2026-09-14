"""Generate a deterministic, synthetic 100 m city block and web GLB."""

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
    create_box,
    create_building,
    create_material,
    create_road,
    create_sidewalk,
    create_streetlight,
    create_tree,
    export_glb,
    point_camera,
    render_png,
    save_blend,
)


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    clear_scene()
    configure_scene()
    ground = create_material("Ground", (0.13, 0.24, 0.15, 1.0))
    road = create_material("Asphalt", (0.045, 0.052, 0.065, 1.0), roughness=0.94)
    walk = create_material("Concrete", (0.5, 0.51, 0.5, 1.0), roughness=0.88)
    warm = create_material("FacadeWarm", (0.52, 0.22, 0.12, 1.0))
    blue = create_material("FacadeBlue", (0.1, 0.28, 0.46, 1.0), roughness=0.5)
    neutral = create_material("FacadeNeutral", (0.48, 0.44, 0.38, 1.0))
    trunk = create_material("TreeTrunk", (0.18, 0.075, 0.035, 1.0))
    leaves = create_material("TreeLeaves", (0.06, 0.27, 0.09, 1.0))
    metal = create_material("StreetlightPole", (0.1, 0.11, 0.13, 1.0), metallic=0.55)
    lamp = create_material("StreetlightLamp", (0.95, 0.74, 0.25, 1.0), roughness=0.35)

    create_box("BlockGround", (0, 0, -0.2), (100, 100, 0.4), ground)
    create_road("EastWestRoad", 0, 0, 14, 100, "x", road)
    create_road("NorthSouthRoad", 0, 0, 14, 100, "y", road)
    for name, x, y, orientation in (
        ("WalkN", 0, 8.5, "x"), ("WalkS", 0, -8.5, "x"),
        ("WalkE", 8.5, 0, "y"), ("WalkW", -8.5, 0, "y"),
    ):
        create_sidewalk(name, x, y, 3, 100, orientation, walk)

    buildings = [
        ("B01", -33, -31, 22, 19, 18, warm),
        ("B02", -32, 28, 20, 25, 34, blue),
        ("B03", 28, -31, 25, 18, 25, neutral),
        ("B04", 31, 29, 18, 22, 42, warm),
        ("B05", 16, 30, 10, 17, 15, blue),
        ("B06", -18, -31, 7, 12, 11, neutral),
    ]
    for args in buildings:
        create_building(*args)

    tree_positions = [(-44, -12), (-33, -12), (-22, -12), (22, 12), (33, 12), (44, 12), (-12, 20), (-12, 33), (12, -20), (12, -34)]
    for index, (x, y) in enumerate(tree_positions):
        create_tree(f"Tree{index:02d}", x, y, trunk, leaves)

    light_positions = [(-42, 11), (-22, 11), (22, -11), (42, -11), (11, 40), (11, 20), (-11, -20), (-11, -40)]
    for index, (x, y) in enumerate(light_positions):
        create_streetlight(f"Streetlight{index:02d}", x, y, metal, lamp)

    add_daylight()
    camera = add_camera("ProceduralCamera", (104, -116, 104), (0, 0, 9), lens=50)
    scene_path = ROOT / "blender" / "scenes" / "procedural-block-test.blend"
    save_blend(scene_path)
    render_png(ROOT / "blender" / "renders" / "procedural-block-aerial.png")
    camera.location = (2, -54, 8.5)
    camera.data.lens = 38
    point_camera(camera, (4, 15, 6.0))
    render_png(ROOT / "blender" / "renders" / "procedural-block-street.png")
    export_glb(ROOT / "exports" / "glb" / "integration-test.glb")
    print("BGC_PIPELINE: procedural block and GLB complete")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
