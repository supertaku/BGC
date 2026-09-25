"""PSE calibration geometry, pending source-camera matching and visual signoff.

Only coarse OSM volumes and the architect-documented frontpiece/rib idea are
represented here. Rib spacing and edge assignment are inferred and must be
checked against source-matched views before this asset can be approved.
"""

from __future__ import annotations

import math
import json
from pathlib import Path

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

    parameters = spec.get("landmark_parameters", {})
    for component in ("body", "frontpiece"):
        if parameters.get(f"{component}_top", {}).get("type") != "FLAT":
            raise ValueError(f"Unsupported PSE {component} upper form; review evidence before modeling")
    analysis_path = Path(__file__).resolve().parents[2] / "data/reports/pse-part-analysis.json"
    partition = json.loads(analysis_path.read_text(encoding="utf-8"))["massing_partition_hypothesis"]
    if partition["body_source_id"] != BODY or partition["frontpiece_source_id"] != FRONTPIECE:
        raise ValueError("PSE part analysis source IDs do not match the builder")

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
            if component == "body":
                polygons = [[partition["body_residual_ring_m"]]]
            obj = tools.create_extruded_polygons(
                f"PSE_{component}", polygons, 0.0, height,
                materials[family], "inferred body/frontpiece partition from mapped OSM overlap")
            status = "INFERRED"
            observation_ids = [f"obs:{entity}:footprint", f"obs:{entity}:height",
                               f"obs:{entity}:part-interpretation"]
            evidence_ids = ["source:osm", ARCHITECT_REF]
        tag(obj, f"{entity}:{component}", "massing", status,
            observation_ids, evidence_ids)

    if spec["builder_strategy"].get("phase") == "MASSING":
        return objects

    # A single spine receives vertical expression. Edge and count are an
    # explicit modeling hypothesis, not a measured architectural dimension.
    edge_index = parameters.get("principal_facade_edge", {}).get("index")
    if edge_index is None:
        raise ValueError("PSE principal facade edge is unresolved; facade phase cannot proceed")
    ring = tools.geojson_polygons(geometry[FRONTPIECE]["geometry"])[0][0]
    frame = PolygonEdgeFrame.from_ring(ring, edge_index, 131.0)
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
