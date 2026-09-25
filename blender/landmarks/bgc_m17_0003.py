"""PSE calibration geometry, pending source-camera matching and visual signoff.

Only coarse OSM volumes and the architect-documented frontpiece/rib idea are
represented here. Rib spacing and edge assignment are inferred and must be
checked against source-matched views before this asset can be approved.
"""

from __future__ import annotations

import math
import bpy

from blender.framework.geometry import PolygonEdgeFrame
from blender.framework.metadata import apply_component_metadata


PODIUM = "osm:way:71598335"
BODY = "osm:way:538701627"
FRONTPIECE = "osm:way:1069827306"
ARCHITECT_REF = "ref:m16r:architect-pse"


def build(context: dict) -> list:
    tools = context["scene_tools"]
    geometry = context["geometry_by_id"]
    materials = context["materials"]
    spec = context["spec"]
    entity = context["entity_id"]
    objects = []

    def tag(obj, component: str, kind: str, status: str, observations: list[str], evidence: list[str]):
        apply_component_metadata(
            obj, entity_id=entity, component_id=component, component_type=kind,
            evidence_status=status, observation_ids=observations, evidence_ids=evidence,
            reconstruction_fidelity=spec["target_fidelity"],
            target_time_state=spec["target_time_state"]["value"],
        )
        objects.append(obj)

    # The residual outline is the mapped three-level base. The two upper mapped
    # parts are retained as distinct source volumes; their overlap is a known
    # massing discrepancy for the first reference-matched review.
    def sloped_volume(name, polygon, height, slope, material):
        ring = list(polygon[0])
        if ring[0] == ring[-1]:
            ring.pop()
        signed_area = sum(ring[i][0] * ring[(i + 1) % len(ring)][1]
                          - ring[(i + 1) % len(ring)][0] * ring[i][1]
                          for i in range(len(ring)))
        if signed_area < 0:
            ring.reverse()
        diagonals = [x - y for x, y in ring]
        lo, hi = min(diagonals), max(diagonals)
        tops = [height - slope * (value - lo) / max(hi - lo, .001) for value in diagonals]
        n = len(ring)
        vertices = [(x, y, 0.0) for x, y in ring] + [
            (x, y, tops[i]) for i, (x, y) in enumerate(ring)]
        faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
        faces += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
        mesh = bpy.data.meshes.new(f"{name}_mesh")
        mesh.from_pydata(vertices, [], faces)
        mesh.validate(clean_customdata=True)
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        obj.data.materials.append(material)
        return obj

    for source_id, height, family, component in (
        (PODIUM, 15.6, "light_neutral_panel", "podium"),
        (BODY, 119.2, "architectural_dark_glass", "body"),
        (FRONTPIECE, 131.0, "architectural_dark_glass", "frontpiece"),
    ):
        shape = geometry[source_id]["geometry"]
        polygons = tools.geojson_polygons(shape)
        if component == "podium":
            obj = tools.create_extruded_polygons(
                f"PSE_{component}", polygons, 0.0, height,
                materials[family], "mapped footprint and OSM height")
            status = "VERIFIED_GEOGRAPHIC"
            observation_ids = [f"obs:{entity}:footprint", f"obs:{entity}:height"]
            evidence_ids = ["source:osm"]
        else:
            obj = sloped_volume(f"PSE_{component}", polygons[0], height,
                                spec.get("landmark_parameters", {}).get("roof_slope_m", 0.0),
                                materials[family])
            status = "INFERRED"
            observation_ids = [f"obs:{entity}:footprint", f"obs:{entity}:height",
                               f"obs:{entity}:roof-slope"]
            evidence_ids = ["source:osm", ARCHITECT_REF]
        tag(obj, f"{entity}:{component}", "massing", status,
            observation_ids, evidence_ids)

    if spec["builder_strategy"].get("phase") == "MASSING":
        return objects

    # A single spine receives vertical expression. Edge and count are an
    # explicit modeling hypothesis, not a measured architectural dimension.
    ring = tools.geojson_polygons(geometry[FRONTPIECE]["geometry"])[0][0]
    frame = PolygonEdgeFrame.from_ring(ring, 0, 131.0)
    for index in range(8):
        u = (index + 0.5) / 8
        placement = frame.region(max(0, u - .018), min(1, u + .018), .12, .95, .62)
        obj = tools.create_box(
            f"PSE_spine_rib_{index:02d}",
            (*placement["center_xy"], placement["center_z"]),
            (max(.45, placement["width_m"]), .78, placement["height_m"]),
            materials["light_neutral_panel"],
        )
        obj.rotation_euler[2] = math.radians(placement["angle_deg"])
        obj["runtime_group"] = "PSE_SPINE_RIBS"
        tag(obj, f"{entity}:spine-rib:{index:02d}", "facade_region", "INFERRED",
            [f"obs:{entity}:ribs"], [ARCHITECT_REF])
    return objects
