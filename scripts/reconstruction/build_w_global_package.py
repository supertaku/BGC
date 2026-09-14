"""Build the grounded W Global Center reconstruction package from cached data.

This script stores observations and URLs only for copyrighted visual sources.
It never downloads or redistributes their images.
"""

from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ENTITY_ID = "bgc_building_0007"
PACKAGE = ROOT / "data" / "reconstruction_packages" / ENTITY_ID
SOURCE_FEATURE = "osm:way:145147831"


def write(name: str, value: object) -> None:
    PACKAGE.mkdir(parents=True, exist_ok=True)
    (PACKAGE / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def distance(a: list[float], b: list[float]) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])


def polygon_metrics(ring: list[list[float]]) -> dict:
    points = ring[:-1] if ring[0] == ring[-1] else ring
    twice_area = sum(
        points[i][0] * points[(i + 1) % len(points)][1]
        - points[(i + 1) % len(points)][0] * points[i][1]
        for i in range(len(points))
    )
    area = abs(twice_area) / 2
    perimeter = sum(distance(points[i], points[(i + 1) % len(points)]) for i in range(len(points)))
    factor = 1 / (3 * twice_area)
    cx = factor * sum(
        (points[i][0] + points[(i + 1) % len(points)][0])
        * (points[i][0] * points[(i + 1) % len(points)][1] - points[(i + 1) % len(points)][0] * points[i][1])
        for i in range(len(points))
    )
    cy = factor * sum(
        (points[i][1] + points[(i + 1) % len(points)][1])
        * (points[i][0] * points[(i + 1) % len(points)][1] - points[(i + 1) % len(points)][0] * points[i][1])
        for i in range(len(points))
    )
    edges = sorted((distance(points[i], points[(i + 1) % len(points)]) for i in range(len(points))), reverse=True)
    longest_index = max(range(len(points)), key=lambda i: distance(points[i], points[(i + 1) % len(points)]))
    dx = points[(longest_index + 1) % len(points)][0] - points[longest_index][0]
    dy = points[(longest_index + 1) % len(points)][1] - points[longest_index][1]
    angle = math.degrees(math.atan2(dy, dx))
    if angle >= 90:
        angle -= 180
    if angle < -90:
        angle += 180
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    return {
        "area_m2": round(area, 2),
        "perimeter_m": round(perimeter, 2),
        "centroid_local_m": {"x": round(cx, 3), "y": round(cy, 3)},
        "oriented_bounding_box_m": {"major": round(sum(edges[:2]) / 2, 3), "minor": round(sum(edges[2:]) / 2, 3)},
        "local_axis_rotation_deg_from_east": round(angle, 3),
        "major_axis_bearing_deg_clockwise_from_north": round((90 - angle) % 180, 3),
        "axis_aligned_bounds_m": {"min_x": min(xs), "min_y": min(ys), "max_x": max(xs), "max_y": max(ys)},
        "major_edge_lengths_m": [round(value, 3) for value in edges],
    }


def ref(reference_id: str, source_id: str, title: str, url: str, role: str, viewpoint: str, facades: list[str]) -> dict:
    return {
        "reference_id": reference_id,
        "source_id": source_id,
        "entity_links": [{"entity_id": ENTITY_ID, "relationship": role, "confidence": 0.95}],
        "source_page_url": url,
        "title": title,
        "reference_role": role,
        "entity_match_status": "ACCEPTED",
        "appearance_period": "CURRENT_OR_RECENT",
        "storage_status": "REMOTE_METADATA_ONLY",
        "rights_status": "RESEARCH_ONLY",
        "viewable_for_research": True,
        "directional_evidence": {
            "viewpoint_side": viewpoint,
            "facades_visible": facades,
            "target_visibility": "HIGH",
            "occlusion": "LOW_TO_MODERATE",
            "perspective_quality": "GOOD_OBLIQUE",
            "camera_match_feasibility": "PARTIAL",
        },
    }


def observation(obs_id: str, prop: str, value: object, status: str, confidence: float, sources: list[str], refs: list[str], method: str, notes: str | None = None) -> dict:
    return {
        "observation_id": obs_id, "entity_id": ENTITY_ID, "property": prop,
        "value": value, "status": status, "confidence": confidence,
        "source_ids": sources, "reference_ids": refs, "method": method, "notes": notes,
    }


def main() -> None:
    geo = json.loads((ROOT / "data" / "processed" / "pilot-buildings.geojson").read_text(encoding="utf-8"))
    feature = next(item for item in geo["features"] if item.get("id") == SOURCE_FEATURE)
    ring = feature["geometry"]["coordinates"][0]
    metrics = polygon_metrics(ring)
    geometry = {
        "type": "FeatureCollection", "projected_crs": "EPSG:32651", "units": "metres",
        "origin_wgs84": {"longitude": 121.050972, "latitude": 14.550806},
        "features": [feature], "deterministic_measurements": metrics,
    }
    write("geometry.geojson", geometry)

    references = [
        ref("ref:official:w-global", "source:official-w-group-w-global", "W Global Center", "https://wgroup.com.ph/projects/w-global-center-3/", "IDENTITY_FACTS_AND_EXTERIOR", "CORNER_30TH_9TH", ["30TH_STREET", "9TH_AVENUE"]),
        ref("ref:web:officepro-w-global", "source:officepro-w-global", "W Global Center gallery", "https://www.officepro.ph/buildings/w-global-center", "MULTI_VIEW_EXTERIOR", "CORNER_30TH_9TH", ["30TH_STREET", "9TH_AVENUE"]),
        ref("ref:web:colliers-w-global", "source:colliers-w-global", "W Global Center listing", "https://www.colliers.com/en-ph/properties/office-space-for-lease-in-bonifacio-global-city-taguig/phl-w-global-center/phl22000360", "EXTERIOR_AND_BUILDING_FACTS", "CORNER_30TH_9TH", ["30TH_STREET", "9TH_AVENUE"]),
        ref("ref:web:savills-w-global", "source:savills-w-global", "W Global Center building details", "https://savillsph.com/building/w-global-center/", "BUILDING_FACTS_AND_EXTERIOR", "CORNER_30TH_9TH", ["30TH_STREET", "9TH_AVENUE"]),
        ref("ref:web:kmc-w-global-brochure", "source:kmc-w-global-brochure", "W Global Center 2014 brochure", "https://www.slideshare.net/slideshow/w-global-center/40801947", "FLOOR_ORGANIZATION_AND_HISTORIC_EXTERIOR", "CORNER_30TH_9TH", ["30TH_STREET", "9TH_AVENUE"]),
    ]
    write("references.json", {"schema_version": 2, "generated_at": "2026-09-14", "records": references})
    write("rights.json", {"schema_version": 2, "references": [{
        "reference_id": item["reference_id"], "rights_status": "RESEARCH_ONLY",
        "local_copy_allowed": False, "derivative_use_allowed": False,
        "redistribution_allowed": False, "commercial_use_allowed": False,
        "rights_notes": "Publicly viewable copyrighted property media; observations and URL only.",
    } for item in references]})

    observations = [
        observation("obs:wgc:identity", "identity", "W Global Center at 9th Avenue corner 30th Street", "VERIFIED_AUTHORITATIVE", 0.99, ["source:official-w-group-w-global", "source:osm", "source:wikidata"], ["ref:official:w-global"], "owner_geographic_identifier_reconciliation"),
        observation("obs:wgc:footprint", "footprint_metrics", metrics, "VERIFIED_GEOGRAPHIC", 0.8, ["source:osm"], [], "deterministic_local_metre_polygon_measurement", "Community-mapped geometry; not cadastral."),
        observation("obs:wgc:height", "height_m", 30.5, "VERIFIED_GEOGRAPHIC", 0.75, ["source:osm"], [], "explicit_osm_height_tag", "Retained unchanged; not a surveyed measurement."),
        observation("obs:wgc:floor-conflict", "physical_storey_count", {
            "claims": [
                {"value": 7, "source": "owner and Colliers"},
                {"value": 8, "source": "OSM building:levels, Savills, and OfficePro"},
            ],
            "possible_explanation": "Ground/mezzanine or marketing-count convention; not determinable from available sources.",
            "final_modeling_interpretation": "Unresolved; follow visible architectural bands inside the 30.5 m envelope.",
        }, "CONFLICTED", 0.78, ["source:official-w-group-w-global", "source:colliers-w-global", "source:savills-w-global", "source:officepro-w-global", "source:osm"], ["ref:official:w-global", "ref:web:colliers-w-global", "ref:web:savills-w-global", "ref:web:officepro-w-global"], "cross_source_conflict_audit"),
        observation("obs:wgc:floor-organization", "visible_and_published_floor_organization", {"ground_and_mezzanine": "retail/dining", "open_bands": 2, "brochure_interpretation": "two parking levels", "upper_office_window_rows": "approximately four visible rows"}, "VERIFIED_PHOTOGRAPHIC", 0.84, ["source:kmc-w-global-brochure", "source:officepro-w-global"], ["ref:web:kmc-w-global-brochure", "ref:web:officepro-w-global"], "brochure_and_multi_view_visual_reconciliation", "Open bands are geometrically verified; their parking use is supported by the brochure, not inferred from appearance alone."),
        observation("obs:wgc:massing", "overall_massing", "Rectangular low-rise office block with transparent retail base, two open horizontal middle bands, an opaque upper office volume, a glazed corner zone, and a projecting rooftop square frame.", "VERIFIED_PHOTOGRAPHIC", 0.9, ["source:officepro-w-global", "source:colliers-w-global"], ["ref:web:officepro-w-global", "ref:web:colliers-w-global"], "multi_view_visual_reconciliation"),
        observation("obs:wgc:facades", "street_facades", {"30TH_STREET": "light panel grid with regular punched windows, open middle bands and glazed base", "9TH_AVENUE": "light panels, regular punched windows, broad upper glazing zone and open middle bands", "corner": "full-height glazed office corner above open bands; square rooftop frame"}, "VERIFIED_PHOTOGRAPHIC", 0.88, ["source:officepro-w-global", "source:colliers-w-global"], ["ref:web:officepro-w-global", "ref:web:colliers-w-global"], "three_oblique_exterior_views"),
        observation("obs:wgc:materials", "material_families", ["light neutral opaque panels", "blue/dark architectural glass", "dark structural metal", "clear-to-dark storefront glass", "neutral concrete slabs"], "VERIFIED_PHOTOGRAPHIC", 0.87, ["source:officepro-w-global"], ["ref:web:officepro-w-global"], "visual_material_family_classification", "Exact colours and reflectance remain unknown."),
        observation("obs:wgc:entrance", "primary_public_entrance", "Glazed ground-level public/retail frontage near the 30th Street–9th Avenue corner; exact portal hierarchy and width unresolved.", "INFERRED", 0.62, ["source:officepro-w-global"], ["ref:web:officepro-w-global"], "oblique_visual_interpretation"),
        observation("obs:wgc:roof", "roof_feature", "Large square open frame rises above the glazed corner; fine roof equipment is not resolved.", "VERIFIED_PHOTOGRAPHIC", 0.86, ["source:officepro-w-global", "source:colliers-w-global"], ["ref:web:officepro-w-global", "ref:web:colliers-w-global"], "multiple_oblique_views"),
        observation("obs:wgc:architect", "architect_or_designer", "Esteban Tan & Associates", "INFERRED", 0.45, ["source:official-w-group-w-global"], ["ref:official:w-global"], "bounded_search_no_primary_project_credit_found", "The attribution was not independently supported by an original firm/project page; do not present it as verified."),
    ]
    write("observations.json", {"schema_version": 2, "observations": observations, "conflicts": ["obs:wgc:floor-conflict"]})

    entity = {
        "entity_id": ENTITY_ID, "entity_type": "BUILDING", "canonical_name": "W Global Center",
        "aliases": ["W Global Center"], "status": "ACTIVE", "identity_status": "CONFIRMED",
        "identity_confidence": 0.99, "decision_method": "DIRECT_IDENTIFIER_AND_OWNER_LOCATION_MATCH",
        "centroid": {"longitude": 121.0518762, "latitude": 14.5511718, **metrics["centroid_local_m"]},
        "footprint_reference": "data/processed/pilot-buildings.geojson", "geographic_feature_ids": [SOURCE_FEATURE],
        "osm_ids": [SOURCE_FEATURE], "building_part_ids": [], "wikidata_id": "Q18395924",
        "official_url": "https://wgroup.com.ph/projects/w-global-center-3/",
        "official_address": "9th Avenue corner 30th Street, BGC, Taguig",
        "source_ids": ["source:osm", "source:wikidata", "source:official-w-group-w-global"],
        "height": {"value_m": 30.5, "status": "VERIFIED_GEOGRAPHIC", "method": "osm_height", "confidence": 0.75, "source_ids": ["source:osm"], "levels": 8},
        "reconstruction_package_version": 1, "target_time_state": "CURRENT_APPROX_2025_2026",
        "reconstruction_readiness": "RECONSTRUCTION_READY_WITH_GAPS",
    }
    write("entity.json", entity)

    materials = [
        ("mat:light-panel", "light neutral opaque architectural panels", "light_neutral_panel"),
        ("mat:dark-glazing", "dark blue reflective architectural glass", "architectural_dark_glass"),
        ("mat:storefront-glazing", "clear-to-dark storefront glazing", "generic_storefront_glass"),
        ("mat:dark-metal", "dark structural metal", "dark_metal"),
        ("mat:neutral-concrete", "neutral concrete/open-deck surfaces", "neutral_roof"),
    ]
    write("materials.json", {"schema_version": 1, "entity_id": ENTITY_ID, "materials": [{"material_id": i, "family": f, "shared_family": s, "status": "VERIFIED_PHOTOGRAPHIC", "confidence": 0.84, "evidence_ids": ["ref:web:officepro-w-global"], "exact_colour": "UNKNOWN"} for i, f, s in materials]})

    facade_defs = [
        ("wgc:facade:30th", "30TH_STREET", "GOOD", ["regular punched office windows", "open horizontal middle bands", "glazed retail base", "glazed corner zone"]),
        ("wgc:facade:9th", "9TH_AVENUE", "GOOD", ["regular punched office windows", "broad upper glazing", "open horizontal middle bands", "glazed retail base"]),
        ("wgc:facade:opposite-a", "OPPOSITE_SIDE_A", "WEAK", ["massing-only conservative treatment"]),
        ("wgc:facade:opposite-b", "OPPOSITE_SIDE_B", "WEAK", ["massing-only conservative treatment"]),
    ]
    write("facades.json", {"schema_version": 1, "entity_id": ENTITY_ID, "facades": [{
        "facade_id": i, "orientation": o, "major_segments": segs,
        "floor_alignment": "Follow visible bands; physical storey count remains CONFLICTED",
        "bay_count": "APPROXIMATE_FROM_PHOTOGRAPHY" if rating == "GOOD" else "UNKNOWN",
        "opening_pattern": "regular office rhythm" if rating == "GOOD" else "UNKNOWN",
        "material_regions": ["mat:light-panel", "mat:dark-glazing", "mat:storefront-glazing", "mat:dark-metal", "mat:neutral-concrete"],
        "entrances": ["wgc:entrance:corner-public"] if o == "30TH_STREET" else [],
        "setbacks": ["upper office volume over open bands and retail base"],
        "confidence": 0.86 if rating == "GOOD" else 0.3,
        "status": "VERIFIED_PHOTOGRAPHIC" if rating == "GOOD" else "UNKNOWN",
        "evidence_ids": ["ref:web:officepro-w-global"], "coverage_rating": rating,
    } for i, o, rating, segs in facade_defs]})
    write("entrances.json", {"schema_version": 1, "entity_id": ENTITY_ID, "entrances": [{
        "entrance_id": "wgc:entrance:corner-public", "type": "PUBLIC_APPROACH", "hierarchy": "PRIMARY_CANDIDATE",
        "side": "30TH_STREET", "position": "NEAR_30TH_9TH_CORNER", "status": "INFERRED", "confidence": 0.62,
        "evidence_ids": ["ref:web:officepro-w-global"], "geometry_guidance": "Use an understated glazed opening; do not claim exact portal width or door count.",
    }]})

    massing = {
        "schema_version": 1, "entity_id": ENTITY_ID,
        "coordinate_frame": {"origin_wgs84": {"longitude": 121.050972, "latitude": 14.550806}, "axes": {"x": "east", "y": "north", "z": "up"}, "units": "metres"},
        "target_local_frame": {"centroid_local_m": metrics["centroid_local_m"], "30th_street_side": "northeast short edge", "9th_avenue_side": "northwest long edge", "footprint_rotation_deg_from_east": metrics["local_axis_rotation_deg_from_east"]},
        "known_dimensions": metrics,
        "height_audit": {"source_feature": SOURCE_FEATURE, "original_value": "30.5", "unit": "m", "strength": "EXPLICIT_COMMUNITY_GEOGRAPHIC_NOT_SURVEYED"},
        "components": [
            {"component_id": "wgc:massing:envelope", "geometry_basis": SOURCE_FEATURE, "height_m": 30.5, "height_status": "VERIFIED_GEOGRAPHIC", "confidence": 0.8, "modeling_class": "PARAMETRIC", "evidence": ["source:osm", "ref:web:officepro-w-global"]},
            {"component_id": "wgc:massing:retail-base", "height_range_m": [0, 6.0], "height_status": "ESTIMATED", "confidence": 0.72, "modeling_class": "PARAMETRIC", "evidence": ["ref:web:kmc-w-global-brochure", "ref:web:officepro-w-global"]},
            {"component_id": "wgc:massing:open-bands", "height_range_m": [6.0, 14.0], "height_status": "ESTIMATED", "confidence": 0.84, "modeling_class": "NEW_SHARED_PRIMITIVE", "evidence": ["ref:web:officepro-w-global"]},
            {"component_id": "wgc:massing:office-volume", "height_range_m": [14.0, 30.5], "height_status": "ESTIMATED", "confidence": 0.88, "modeling_class": "PARAMETRIC", "evidence": ["ref:web:officepro-w-global"]},
            {"component_id": "wgc:roof:corner-frame", "height_range_m": [27.8, 30.5], "height_status": "VERIFIED_PHOTOGRAPHIC", "confidence": 0.86, "modeling_class": "TARGET_SPECIFIC_CONFIGURATION", "evidence": ["ref:web:officepro-w-global", "ref:web:colliers-w-global"]},
        ],
        "massing_summary": "Mapped rectangular footprint, transparent retail base, two visually open bands, upper office volume, and a square rooftop corner frame; total height remains 30.5 m.",
    }
    write("massing.json", massing)

    unknowns = [
        ("unknown:wgc:floor-count", "Exact physical storey count and counting convention", "Preserve conflict; model visible bands"),
        ("unknown:wgc:opposite-a", "Opposite side A openings and service functions", "Use low-detail neutral wall"),
        ("unknown:wgc:opposite-b", "Opposite side B openings and service functions", "Use low-detail neutral wall"),
        ("unknown:wgc:entrance", "Exact primary portal width, door count, and hierarchy", "Use understated inferred glazing"),
        ("unknown:wgc:roof-plant", "Rooftop machinery and fine frame connections", "Omit machinery; retain only major square frame"),
        ("unknown:wgc:window-spacing", "Exact centimetre window/mullion spacing", "Use normalized approximate rhythm"),
    ]
    write("unknowns.json", {"schema_version": 2, "unknowns": [{"unknown_id": i, "entity_id": ENTITY_ID, "description": d, "impact": "LOD1_DETAIL", "disposition": a} for i, d, a in unknowns]})

    aspects = {
        "identity": "GOOD", "footprint": "GOOD", "height": "GOOD", "floor_organization": "PARTIAL",
        "overall_massing": "GOOD", "30th_street_side": "GOOD", "9th_avenue_side": "GOOD",
        "opposite_side_a": "WEAK", "opposite_side_b": "WEAK", "primary_entrance": "PARTIAL",
        "entrance": "PARTIAL", "parking_bands": "GOOD", "ground_retail": "PARTIAL", "glazing": "GOOD",
        "opaque_panels": "GOOD", "structural_frame": "PARTIAL", "roof": "GOOD", "materials": "GOOD", "street_context": "PARTIAL",
    }
    gap_records = {name: {"rating": rating, "reference_ids": ["ref:web:officepro-w-global"] if name not in {"footprint", "height"} else [], "confidence": 0.85 if rating == "GOOD" else 0.5 if rating == "PARTIAL" else 0.3, "blocking": False} for name, rating in aspects.items()}
    write("evidence_gaps.json", {"schema_version": 2, "entity_id": ENTITY_ID, "aspects": gap_records, "reconstruction_gate": "RECONSTRUCTION_READY_WITH_GAPS"})
    write("coverage.json", {"schema_version": 2, "entity_id": ENTITY_ID, "accepted_visual_reference_ids": [item["reference_id"] for item in references], "reusable_visual_reference_ids": [], "research_only_visual_reference_ids": [item["reference_id"] for item in references], "aspects": {name: {"rating": rating, "reference_ids": gap_records[name]["reference_ids"]} for name, rating in aspects.items()}, "reconstruction_readiness": "RECONSTRUCTION_READY_WITH_GAPS", "readiness_reason": "Identity, footprint, height, massing, both street sides, corner, open bands, and roof frame are usable. Opposite sides and exact entrance remain weak and must stay conservative."})
    write("timeline.json", {"schema_version": 1, "entity_id": ENTITY_ID, "events": [{"period": "2012", "event": "Building completion reported by current property firms", "status": "VERIFIED_STRUCTURED", "evidence_ids": ["ref:web:colliers-w-global", "ref:web:savills-w-global"]}, {"period": "2025-2026", "event": "Permanent architecture target state; tenant graphics excluded", "status": "INFERRED", "evidence_ids": ["ref:web:officepro-w-global"]}]})

    spec = {
        "schema_version": "1.0", "target": {"entity_id": ENTITY_ID, "name": "W Global Center", "location": "9th Avenue corner 30th Street, BGC, Taguig, Philippines", "identity_status": "CONFIRMED"},
        "target_time_state": {"value": "CURRENT_APPROX_2025_2026", "permanent_architecture": "PRIMARY", "tenant_signage_and_seasonal_state": "OMIT_OR_NEUTRALIZE"},
        "target_fidelity": "LOD1_MEDIUM_ARCHITECTURAL_FIDELITY", "geometry_file": "geometry.geojson",
        "known_dimensions": {**metrics, "maximum_height_m": 30.5, "height_status": "VERIFIED_GEOGRAPHIC_NOT_SURVEYED"},
        "major_building_parts": ["wgc:massing:retail-base", "wgc:massing:open-bands", "wgc:massing:office-volume", "wgc:roof:corner-frame"],
        "massing_file": "massing.json", "facades_file": "facades.json", "entrances_file": "entrances.json", "materials_file": "materials.json",
        "street_relationship": {"30TH_STREET": "northeast short street edge", "9TH_AVENUE": "northwest long street edge", "OPPOSITE_SIDE_A": "weakly evidenced", "OPPOSITE_SIDE_B": "weakly evidenced"},
        "best_reference_ids": ["ref:web:officepro-w-global", "ref:web:colliers-w-global", "ref:web:kmc-w-global-brochure"],
        "required_coverage_aspects": ["overall_massing", "30th_street_side", "9th_avenue_side", "materials"],
        "confidence": {"identity": 0.99, "footprint": 0.8, "height": 0.75, "massing": 0.9, "30th_street": 0.88, "9th_avenue": 0.86, "opposite_a": 0.3, "opposite_b": 0.3, "entrance": 0.62, "roof": 0.86, "materials": 0.87},
        "required_procedural_approximations": [
            {"feature": "office window rhythm", "classification": "PROCEDURAL", "instruction": "Use normalized repeated bays; avoid false centimetre precision."},
            {"feature": "open horizontal bands", "classification": "PROCEDURAL", "instruction": "Use the shared open-facade-band primitive with brochure-supported parking interpretation."},
            {"feature": "opposite facades", "classification": "PROCEDURAL", "instruction": "Use conservative neutral treatment without specific doors or service openings."},
            {"feature": "roof corner frame", "classification": "CUSTOM", "instruction": "Configure a simple square open frame from observed silhouette; omit machinery."},
        ],
        "do_not_invent": ["Do not resolve seven versus eight storeys without new evidence.", "Do not invent service/loading openings on weak sides.", "Do not copy tenant or leasing graphics.", "Do not invent roof machinery.", "Do not claim exact window spacing or entrance dimensions."],
        "visual_qa_cameras": [
            {"camera_id": "qa:wgc:30th", "position": "street-level across 30th Street", "target": "30th Street facade", "fov_deg": 55, "corresponding_reference": "ref:web:officepro-w-global", "confidence": 0.72, "match_status": "PARTIAL"},
            {"camera_id": "qa:wgc:9th", "position": "street-level across 9th Avenue", "target": "9th Avenue facade", "fov_deg": 55, "corresponding_reference": "ref:web:officepro-w-global", "confidence": 0.7, "match_status": "PARTIAL"},
            {"camera_id": "qa:wgc:corner", "position": "opposite 30th Street and 9th Avenue corner", "target": "glazed corner and roof frame", "fov_deg": 55, "corresponding_reference": "ref:web:officepro-w-global", "confidence": 0.8, "match_status": "PARTIAL"},
            {"camera_id": "qa:wgc:weak", "position": "opposite-side diagnostic", "target": "weak facades", "fov_deg": 50, "corresponding_reference": None, "confidence": 0.2, "match_status": "NOT_POSSIBLE_REFERENCE_MISSING"},
            {"camera_id": "qa:wgc:aerial", "position": "oblique aerial", "target": "overall massing and roof", "fov_deg": 55, "corresponding_reference": "ref:web:officepro-w-global", "confidence": 0.55, "match_status": "DIAGNOSTIC"},
        ],
        "web_performance_constraints": {"principle": "LOD and measured runtime cost first", "track": ["triangles", "vertices", "materials", "draw_calls", "GLB_transfer_size", "runtime_nodes"], "instructions": ["reuse shared materials", "merge repeated window groups by facade at runtime", "use no photo textures", "retain semantic authoring components"]},
        "model_recommendation": {"next_model": "SOL", "astra_required": False}, "readiness": "RECONSTRUCTION_READY_WITH_GAPS",
    }
    write("reconstruction_spec.json", spec)
    write("README.md", "# W Global Center reconstruction package\n\nSchema 1.0 package generated by `scripts/reconstruction/build_w_global_package.py`. All exterior photographs are research-only remote references; no copyrighted image is bundled. The 7-versus-8 floor conflict is preserved and geometry follows visible bands within the unchanged 30.5 m mapped-height envelope.\n")
    print(f"W_GLOBAL_PACKAGE: PASS area={metrics['area_m2']} perimeter={metrics['perimeter_m']} readiness=RECONSTRUCTION_READY_WITH_GAPS")


if __name__ == "__main__":
    main()
