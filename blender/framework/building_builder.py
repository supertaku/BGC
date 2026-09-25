"""Generic, spec-driven dry-run builder for simple LOD1 reconstruction packages."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
import traceback

import bpy


ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "blender" / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import scene_tools
from blender.framework.export import export_runtime_glb
from blender.framework.geometry import FacadeFrame, PolygonEdgeFrame
from blender.framework.materials import create_material_family
from blender.framework.metadata import apply_component_metadata
from blender.framework.qa import QACameraSpec, create_qa_cameras
from blender.framework.validation import validate_authoring_scene


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--render", action="store_true")
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return parser.parse_args(argv)


def main() -> None:
    args = arguments()
    package = args.package.resolve()
    spec = json.loads((package / "reconstruction_spec.json").read_text(encoding="utf-8"))
    if spec.get("schema_version") != "1.0":
        raise ValueError(f"PACKAGE_ERROR: unsupported schema_version {spec.get('schema_version')!r}")
    config = spec.get("generic_builder")
    if not isinstance(config, dict):
        raise ValueError("PACKAGE_ERROR: generic_builder configuration is required")
    entity_id = spec["target"]["entity_id"]
    scene_tools.clear_scene()
    scene_tools.configure_scene()
    scene = bpy.context.scene
    scene["entity_id"] = entity_id
    scene["schema_version"] = spec["schema_version"]
    scene["source_package"] = str(package.relative_to(ROOT)).replace("\\", "/")
    materials = {family: create_material_family(scene_tools, family) for family in config["material_families"]}
    objects = []
    geometry = json.loads((package / spec["geometry_file"]).read_text(encoding="utf-8"))
    geometry_by_id = {
        feature.get("id") or feature.get("properties", {}).get("id"): feature
        for feature in geometry["features"]
        if feature.get("id") or feature.get("properties", {}).get("id")
    }
    for volume in config.get("polygon_volumes", []):
        feature = geometry_by_id[volume["source_feature_id"]]
        obj = scene_tools.create_extruded_polygons(
            volume["name"], scene_tools.geojson_polygons(feature["geometry"]),
            volume.get("base_z_m", 0.0), volume["height_m"],
            materials[volume["material_family"]], volume["classification"],
        )
        apply_component_metadata(
            obj, entity_id=entity_id, component_id=volume["component_id"],
            component_type="massing", evidence_status=volume["evidence_status"],
            observation_ids=volume["observation_ids"], evidence_ids=volume.get("evidence_ids", []),
            reconstruction_fidelity=spec["target_fidelity"], target_time_state=spec["target_time_state"]["value"],
        )
        objects.append(obj)
    for volume in config["volumes"]:
        obj = scene_tools.create_box(
            volume["name"], tuple(volume["center_m"]), tuple(volume["dimensions_m"]),
            materials[volume["material_family"]],
        )
        apply_component_metadata(
            obj, entity_id=entity_id, component_id=volume["component_id"],
            component_type="massing", evidence_status=volume["evidence_status"],
            observation_ids=volume["observation_ids"], evidence_ids=volume.get("evidence_ids", []),
            reconstruction_fidelity=spec["target_fidelity"],
            target_time_state=spec["target_time_state"]["value"],
        )
        objects.append(obj)
    for band in config.get("polygon_edge_regions", []):
        feature = geometry_by_id[band["source_feature_id"]]
        polygons = scene_tools.geojson_polygons(feature["geometry"])
        for polygon_index, polygon in enumerate(polygons):
            ring = polygon[0]
            edge_count = len(ring) - 1 if ring and ring[0] == ring[-1] else len(ring)
            edge_indices = range(edge_count) if band.get("edges") == "all" else band["edges"]
            for edge_index in edge_indices:
                frame = PolygonEdgeFrame.from_ring(ring, edge_index, band["height_m"])
                placement = frame.region(
                    band.get("u0", 0.0), band.get("u1", 1.0), band["v0"], band["v1"], band.get("d_m", 0.0),
                )
                component_id = f"{band['component_id']}:p{polygon_index}:e{edge_index}"
                obj = scene_tools.create_box(
                    f"{band['name']}_P{polygon_index:02d}_E{edge_index:02d}",
                    (*placement["center_xy"], band.get("base_z_m", 0.0) + placement["center_z"]),
                    (placement["width_m"], band["thickness_m"], placement["height_m"]),
                    materials[band["material_family"]],
                )
                obj.rotation_euler[2] = math.radians(placement["angle_deg"])
                obj["runtime_group"] = band.get("runtime_group", "")
                apply_component_metadata(
                    obj, entity_id=entity_id, component_id=component_id,
                    component_type="facade_region", evidence_status=band["evidence_status"],
                    observation_ids=band["observation_ids"], evidence_ids=band.get("evidence_ids", []),
                    reconstruction_fidelity=spec["target_fidelity"], target_time_state=spec["target_time_state"]["value"],
                )
                objects.append(obj)
    for region in config.get("facade_regions", []):
        frame = FacadeFrame(
            origin=tuple(region["frame"]["origin_m"]), length_m=region["frame"]["length_m"],
            height_m=region["frame"]["height_m"], angle_deg=region["frame"]["angle_deg"],
            outward_sign=region["frame"].get("outward_sign", 1.0),
        )
        placement = frame.region(region["u0"], region["u1"], region["v0"], region["v1"], region.get("d_m", 0.0))
        obj = scene_tools.create_box(
            region["name"], (*placement["center_xy"], placement["center_z"]),
            (placement["width_m"], region["thickness_m"], placement["height_m"]),
            materials[region["material_family"]],
        )
        obj.rotation_euler[2] = math.radians(frame.angle_deg)
        apply_component_metadata(
            obj, entity_id=entity_id, component_id=region["component_id"],
            component_type="facade_region", evidence_status=region["evidence_status"],
            observation_ids=region["observation_ids"], evidence_ids=region.get("evidence_ids", []),
            reconstruction_fidelity=spec["target_fidelity"], target_time_state=spec["target_time_state"]["value"],
        )
        objects.append(obj)
    camera_specs = [QACameraSpec(
        item["camera_id"], item["kind"], tuple(item["location"]), tuple(item["target"]),
        item["lens_mm"], item["filename"], item["match"], tuple(item.get("reference_ids", [])),
    ) for item in config["qa_cameras"]]
    render_dir = ROOT / "blender" / "renders" / entity_id if args.render else None
    if render_dir is not None:
        world = scene.world
        world.use_nodes = True
        background = world.node_tree.nodes.get("Background")
        if background:
            background.inputs["Color"].default_value = (0.55, 0.65, 0.73, 1.0)
            background.inputs["Strength"].default_value = 0.9
        sun_data = bpy.data.lights.new("QA_Sun", type="SUN")
        sun_data.energy = 2.2
        sun = bpy.data.objects.new("QA_Sun", sun_data)
        scene.collection.objects.link(sun)
        sun.rotation_euler = (math.radians(30), math.radians(-20), math.radians(-35))
        sun["exportable"] = False
    create_qa_cameras(scene_tools, camera_specs, render_dir)
    validation = validate_authoring_scene(objects, set(materials.values()))
    if validation["status"] == "FAIL":
        raise RuntimeError(f"GEOMETRY_ERROR: {validation['errors']}")
    scene_path = ROOT / "blender" / "scenes" / f"{entity_id}-lod1.blend"
    glb_path = ROOT / "exports" / "glb" / "buildings" / f"{entity_id}_lod1.glb"
    scene_tools.save_blend(scene_path)
    merge_groups = {}
    for obj in objects:
        group = obj.get("runtime_group")
        if group:
            merge_groups.setdefault(group, []).append(obj.get("component_id"))
    export_report = export_runtime_glb(glb_path, objects, merge_groups)
    report_path = ROOT / "data" / "reports" / "buildings" / f"{entity_id}-dry-run.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps({
        "schema_version": 1, "entity_id": entity_id, "status": "PASS",
        "component_count": len(objects), "materials": len(materials),
        "qa_cameras": len(camera_specs), "authoring_validation": validation,
        "export": export_report,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"GENERIC_BUILD: PASS entity={entity_id} components={len(objects)} materials={len(materials)}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
