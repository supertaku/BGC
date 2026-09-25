"""Rank whole-BGC buildings and prepare the bounded M17 reconstruction batch.

The whole-city pass uses only the immutable processed OSM snapshot.  Web evidence is
represented only for the ten explicitly selected targets and remains metadata-only.
"""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
import json
import math
from pathlib import Path

from shapely.geometry import shape


ROOT = Path(__file__).resolve().parents[2]
TODAY = "2026-09-15"
HIGH_STREET_X = -120.0
HIGH_STREET_Y_RANGE = (-360.0, 360.0)

# asset id, source owner, wave, archetype, complexity, base/accent families,
# facade rhythm, bounded research references
TARGETS = [
    ("bgc_m17_0001", "osm:way:1078392706", "A", "MIXED_USE_PODIUM", "HIGH", "warm_neutral_cladding", "generic_storefront_glass", 3,
     [("official-ayala-obhs", "Ayala Malls — One Bonifacio High Street", "https://www.ayalamalls.com/explore/ayala-bonifacio-high-street/store/AYALA-ONE-BONIFACIO-HIGH-STREET-1326575"), ("architect-obhs", "Handel Architects — One Bonifacio High Street", "https://handelarchitects.com/latest/one-bonifacio-high-street-in-manila-breaks-ground")]),
    ("bgc_m17_0002", "osm:way:203910666", "A", "PODIUM_TOWER", "HIGH", "light_neutral_panel", "architectural_dark_glass", 8,
     [("official-alp-suites", "Ayala Land Premier — The Suites", "https://www.ayala-land-premier.com/the-suites-bonifacio-global-city.html"), ("architect-suites", "Handel Architects — The Suites", "https://www.handelarchitects.com/project/the-suites-at-one-bonifacio-high-street?pagi=residential")]),
    ("bgc_m17_0003", "osm:way:71598335", "A", "OFFICE_LANDMARK", "MEDIUM", "light_neutral_panel", "architectural_dark_glass", 5,
     [("official-pse-tower", "Philippine Stock Exchange — BGC headquarters", "https://www.pse.com.ph/pse-begins-trading-at-bgc-headquarters/"), ("architect-obhs", "Handel Architects — One Bonifacio High Street", "https://handelarchitects.com/latest/one-bonifacio-high-street-in-manila-breaks-ground")]),
    ("bgc_m17_0004", "osm:way:182331875", "A", "OFFICE_TOWER", "HIGH", "architectural_dark_glass", "dark_metal", 7,
     [("official-arthaland-acpt", "Arthaland — Century Pacific Tower", "https://arthaland.com/properties/arthaland-century-pacific-tower"), ("architect-som-acpt", "SOM — Arthaland Century Pacific Tower", "https://www.som.com/projects/arthaland-century-pacific-tower/")]),
    ("bgc_m17_0005", "osm:way:469845356", "B", "HOTEL_PODIUM_TOWER", "HIGH", "light_neutral_panel", "architectural_dark_glass", 8,
     [("official-shang-properties", "Shang Properties — Shangri-La at the Fort", "https://www.shangproperties.com/hospitalities/shangri-la-at-the-fort/"), ("architect-handel-shang", "Handel Architects — Shangri-La at the Fort", "https://handelarchitects.com/project/shangri-la-at-the-fort")]),
    ("bgc_m17_0006", "osm:way:183463814", "B", "CULTURAL_IRREGULAR", "MEDIUM", "light_neutral_panel", "dark_metal", 3,
     [("official-mind-museum", "The Mind Museum", "https://www.themindmuseum.org/"), ("project-mind-museum", "Atlas Concorde — Mind Museum project", "https://www.atlasconcorde.com/en/projects/mind-museum")]),
    ("bgc_m17_0007", "osm:way:25006899", "B", "PERFORMING_ARTS", "MEDIUM", "warm_neutral_cladding", "generic_storefront_glass", 3,
     [("official-bgc-arts-spaces", "BGC Arts Center — Spaces", "https://www.bgcartscenter.org/spaces"), ("official-bgc-arts-about", "BGC Arts Center — About", "https://www.bgcartscenter.org/about")]),
    ("bgc_m17_0008", "osm:way:408450256", "B", "OFFICE_TOWER", "MEDIUM", "light_neutral_panel", "architectural_dark_glass", 6,
     [("official-alveo-hsscp", "Alveo Land — High Street South Corporate Plaza", "https://www.alveoland.com.ph/properties/offices/taguig/hss-corporate-plaza/"), ("official-alveo-bgc", "Alveo Land — BGC properties", "https://www.alveoland.com.ph/commtalk-online/properties-for-sale-taguig-bgc/")]),
    ("bgc_m17_0009", "osm:way:1070584579", "B", "RESIDENTIAL_TOWER", "MEDIUM", "warm_neutral_cladding", "architectural_dark_glass", 7,
     [("official-alveo-maridien", "Alveo Land — High Street South Maridien", "https://www.alveoland.com.ph/properties/condos/taguig/hss-maridien/"), ("official-alveo-bgc", "Alveo Land — BGC properties", "https://www.alveoland.com.ph/commtalk-online/properties-for-sale-taguig-bgc/")]),
    ("bgc_m17_0010", "osm:way:1070584580", "B", "RESIDENTIAL_TOWER", "MEDIUM", "light_neutral_panel", "architectural_dark_glass", 7,
     [("official-alveo-verve", "Alveo Land — Verve Residences", "https://www.alveoland.com.ph/properties/condos/taguig/hss-verve-residences/"), ("official-alveo-bgc", "Alveo Land — BGC properties", "https://www.alveoland.com.ph/commtalk-online/properties-for-sale-taguig-bgc/")]),
]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def point_segment_distance(x: float, y: float) -> float:
    return math.hypot(x - HIGH_STREET_X, y - min(max(y, HIGH_STREET_Y_RANGE[0]), HIGH_STREET_Y_RANGE[1]))


def clamp_score(value: float) -> int:
    return max(0, min(5, round(value)))


def collect_entities() -> tuple[dict[str, list[dict]], dict[str, dict]]:
    features: dict[str, list[dict]] = defaultdict(list)
    for path in sorted((ROOT / "data/processed/bgc-tiles").glob("tile_*.json")):
        for feature in load(path).get("buildings", []):
            features[feature["properties"]["canonical_entity_id"]].append(feature)
    outlines = load(ROOT / "data/processed/bgc-buildings.geojson")["features"]
    source = {item["properties"]["id"]: item for item in outlines}
    return features, source


def rank(features: dict[str, list[dict]], source: dict[str, dict]) -> list[dict]:
    approved_sources = {
        sid for entry in load(ROOT / "data/assets/buildings.json").get("buildings", {}).values()
        if entry.get("available_lods", {}).get("1", {}).get("status") == "APPROVED"
        for sid in entry.get("source_feature_ids", [])
    }
    selected_sources = {item[1] for item in TARGETS}
    records = []
    for entity_id, volumes in features.items():
        outline = source.get(entity_id, volumes[0])
        props = outline["properties"]
        geom = shape(outline["geometry"])
        center = geom.centroid
        name = props.get("name")
        height = max(float(item["properties"].get("height_m", 0)) for item in volumes)
        area = float(props.get("footprint_area_m2") or geom.area)
        vertex_count = len(list(geom.exterior.coords)) - 1 if geom.geom_type == "Polygon" else 8
        distance = point_segment_distance(center.x, center.y)
        named = 1 if name else 0
        landmark = clamp_score(named * 2 + min(height / 85, 2) + min(area / 7000, 1))
        pedestrian = clamp_score(5 - distance / 125)
        tour = clamp_score(5 - math.hypot(center.x + 120, center.y) / 150)
        distinctive = clamp_score(named + min(max(vertex_count - 4, 0) / 3, 2) + (2 if len(volumes) > 1 else 0))
        height_status = props.get("height_status", "UNKNOWN")
        visual_error = clamp_score((3 if height_status == "PROCEDURAL" else 1 if height_status == "ESTIMATED" else 0) + landmark / 2)
        identity = 5 if name and props.get("tags", {}).get("wikidata") else 4 if name else 1
        footprint = clamp_score(float(props.get("footprint_confidence", 0.8)) * 5)
        height_conf = clamp_score(float(props.get("height_confidence", 0.15)) * 5)
        public = clamp_score(named * 2 + (2 if props.get("tags", {}).get("operator") else 0) + (1 if props.get("tags", {}).get("wikidata") else 0))
        complexity = clamp_score(1 + min(vertex_count / 6, 2) + min(len(volumes) - 1, 2) + (1 if height > 100 else 0))
        dimensions = {
            "LANDMARK_IMPORTANCE": landmark, "PEDESTRIAN_VISIBILITY": pedestrian,
            "TOUR_VISIBILITY": tour, "ARCHITECTURAL_DISTINCTIVENESS": distinctive,
            "CURRENT_LOD2_VISUAL_ERROR": visual_error, "IDENTITY_CONFIDENCE": identity,
            "FOOTPRINT_CONFIDENCE": footprint, "HEIGHT_CONFIDENCE": height_conf,
            "PUBLIC_EVIDENCE_AVAILABILITY": public, "RECONSTRUCTION_COMPLEXITY": complexity,
        }
        total = round(landmark * 1.5 + pedestrian * 2 + tour * 1.5 + distinctive + visual_error + identity + footprint + height_conf + public - complexity * .5, 2)
        tier = "A" if entity_id in selected_sources and entity_id in {item[1] for item in TARGETS[:4]} else "B" if entity_id in selected_sources or total >= 34 else "C"
        records.append({
            "entity_id": entity_id, "name": name, "tier": tier, "selected": entity_id in selected_sources,
            "existing_lod1": entity_id in approved_sources, "center_local_m": [round(center.x, 2), round(center.y, 2)],
            "distance_to_high_street_m": round(distance, 2), "height_m": height, "height_status": height_status,
            "footprint_area_m2": round(area, 2), "render_volume_count": len(volumes), "dimensions": dimensions,
            "total_score": total,
        })
    return sorted(records, key=lambda item: (-item["selected"], -item["total_score"], item["entity_id"]))


def metrics(feature: dict) -> dict:
    geom = shape(feature["geometry"])
    x0, y0, x1, y1 = geom.bounds
    return {"area_m2": round(geom.area, 2), "perimeter_m": round(geom.length, 2), "axis_aligned_bounds_m": {"min_x": round(x0, 3), "min_y": round(y0, 3), "max_x": round(x1, 3), "max_y": round(y1, 3)}}


def cameras(feature: dict, asset_id: str, refs: list[str], maximum_height: float) -> tuple[list[dict], list[dict]]:
    x0, y0, x1, y1 = shape(feature["geometry"]).bounds
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    span = max(x1 - x0, y1 - y0, 35)
    height = maximum_height
    offset = max(span * 1.7, height * 2.1)
    specs = []
    visual = []
    for label, location, evidence in (
        ("north", [cx, y1 + offset, max(8, height * .55)], True),
        ("south", [cx, y0 - offset, max(8, height * .55)], False),
        ("east", [x1 + offset, cy, max(8, height * .55)], True),
        ("aerial", [cx + offset * .8, cy - offset * .8, max(28, height * 1.18)], True),
    ):
        reference_ids = refs if evidence else []
        camera_id = f"qa:{asset_id}:{label}"
        target = [cx, cy, height * .45]
        specs.append({"camera_id": camera_id, "kind": "EVIDENCE_MATCH" if evidence else "DIAGNOSTIC", "location": location, "target": target, "lens_mm": 42, "filename": f"qa-{label}.png", "match": "PARTIAL" if evidence else "CONSERVATIVE", "reference_ids": reference_ids})
        visual.append({"camera_id": camera_id, "position": location, "target": target, "fov_deg": 48, "corresponding_reference": refs[0] if evidence else None, "confidence": .72 if evidence else .3, "match_status": "PARTIAL" if evidence else "CONSERVATIVE"})
    return specs, visual


def package_target(target, volumes: list[dict], source: dict[str, dict]) -> dict:
    asset_id, owner_id, wave, archetype, complexity, base_family, accent_family, band_count, refs = target
    owner = source[owner_id]
    name = owner["properties"].get("name") or owner_id
    package = ROOT / "data/reconstruction_packages" / asset_id
    # Preparation may be rerun after a human refines the package. Never replace
    # those evidence and geometry decisions with the initial generic template.
    if (package / "reconstruction_spec.json").exists():
        return {"entity_id": asset_id, "source_entity_id": owner_id, "name": name,
                "tier": "A" if wave == "A" else "B", "wave": wave,
                "archetype": archetype,
                "selection_reason": "High pedestrian/tour visibility and identity-defining massing on or near the High Street experience.",
                "visibility_importance": "VERY_HIGH" if wave == "A" else "HIGH",
                "evidence_readiness": "READY_WITH_GAPS", "expected_complexity": complexity,
                "target_lod": "LOD1", "reference_count": len(refs)}
    reference_records = [{"reference_id": f"ref:m17:{key}", "source_id": f"source:m17:{key}", "title": title, "url": url, "rights_status": "RESEARCH_ONLY", "asset_embedded": False} for key, title, url in refs]
    ref_ids = [item["reference_id"] for item in reference_records]
    package_volumes = deepcopy(volumes)
    for feature in package_volumes:
        # A tile's publication status is runtime state, not source geography.
        feature["properties"].pop("detailed_asset_id", None)
    geometry = {"type": "FeatureCollection", "schema_version": 1, "entity_id": asset_id, "projected_crs": "EPSG:32651", "source_crs": "EPSG:4326", "local_origin_wgs84": [121.050972, 14.550806], "features": package_volumes}
    polygon_volumes = []
    edge_regions = []
    major_parts = []
    for index, volume in enumerate(volumes):
        props = volume["properties"]
        component = f"{asset_id}:massing:{index:02d}"
        major_parts.append(component)
        height = float(props["height_m"]) - float(props.get("min_height_m", 0))
        state = props.get("height_status", "UNKNOWN")
        polygon_volumes.append({"name": f"M17_{asset_id}_Volume_{index:02d}", "component_id": component, "source_feature_id": props["id"], "base_z_m": float(props.get("min_height_m", 0)), "height_m": height, "material_family": base_family, "classification": f"verified geographic footprint; {state.lower()} height", "evidence_status": state, "observation_ids": [f"obs:{asset_id}:footprint", f"obs:{asset_id}:height"], "evidence_ids": ["source:osm"]})
        if height >= 3:
            for band in range(band_count):
                v0 = .08 + band * (.82 / band_count)
                v1 = min(.92, v0 + .045 if height > 45 else v0 + .10)
                edge_regions.append({"name": f"M17_{asset_id}_Band_{index:02d}_{band:02d}", "component_id": f"{asset_id}:facade:{index:02d}:{band:02d}", "source_feature_id": props["id"], "edges": "all", "u0": .03, "u1": .97, "v0": round(v0, 4), "v1": round(v1, 4), "d_m": .08, "thickness_m": .16, "base_z_m": float(props.get("min_height_m", 0)), "height_m": height, "material_family": accent_family, "runtime_group": f"M17_{asset_id}_FACADE", "evidence_status": "INFERRED", "observation_ids": [f"obs:{asset_id}:facade", f"obs:{asset_id}:materials"], "evidence_ids": ref_ids})
    primary = max(volumes, key=lambda item: shape(item["geometry"]).area)
    dims = metrics(primary)
    maximum_height = max(float(item["properties"]["height_m"]) for item in volumes)
    qa_specs, visual_cameras = cameras(primary, asset_id, ref_ids, maximum_height)
    observations = [
        {"observation_id": f"obs:{asset_id}:footprint", "entity_id": asset_id, "property": "footprint", "value": dims, "status": "VERIFIED_GEOGRAPHIC", "confidence": .8, "source_ids": ["source:osm"], "reference_ids": [], "method": "processed_osm_geometry", "notes": "Community-mapped geometry; not cadastral."},
        {"observation_id": f"obs:{asset_id}:height", "entity_id": asset_id, "property": "height_envelope_m", "value": maximum_height, "status": primary["properties"].get("height_status", "UNKNOWN"), "confidence": primary["properties"].get("height_confidence", .15), "source_ids": ["source:osm"], "reference_ids": [], "method": primary["properties"].get("height_method"), "notes": "Retains source evidence status."},
        {"observation_id": f"obs:{asset_id}:facade", "entity_id": asset_id, "property": "major_facade_rhythm", "value": f"{band_count} broad normalized bands", "status": "INFERRED", "confidence": .62, "source_ids": [item["source_id"] for item in reference_records], "reference_ids": ref_ids, "method": "bounded_reference_interpretation", "notes": "Strongest visible facades inform a conservative repeatable rhythm; exact modules are not asserted."},
        {"observation_id": f"obs:{asset_id}:materials", "entity_id": asset_id, "property": "material_families", "value": [base_family, accent_family], "status": "INFERRED", "confidence": .65, "source_ids": [item["source_id"] for item in reference_records], "reference_ids": ref_ids, "method": "bounded_reference_interpretation", "notes": "Broad PBR families only; no photographic textures."},
    ]
    spec = {"schema_version": "1.0", "target": {"entity_id": asset_id, "name": name, "location": "Bonifacio Global City, Taguig, Philippines", "identity_status": "CONFIRMED"}, "target_time_state": {"value": "CURRENT_APPROX_2025_2026", "permanent_architecture": "PRIMARY", "tenant_signage_and_seasonal_state": "OMIT_OR_NEUTRALIZE"}, "target_fidelity": "LOD1_MEDIUM_ARCHITECTURAL_FIDELITY", "geometry_file": "geometry.geojson", "known_dimensions": {**dims, "maximum_height_m": maximum_height, "height_status": primary["properties"].get("height_status", "UNKNOWN")}, "major_building_parts": major_parts, "massing_file": "massing.json", "facades_file": "facades.json", "entrances_file": "entrances.json", "materials_file": "materials.json", "required_coverage_aspects": ["identity", "overall_massing", "major_facades", "roof", "materials", "entrances"], "best_reference_ids": ref_ids, "confidence": {"identity": .92, "footprint": .8, "height": float(primary["properties"].get("height_confidence", .15)), "massing": .72, "materials": .65}, "required_procedural_approximations": [{"feature": "exact facade modules and weak sides", "classification": "PROCEDURAL", "instruction": "Use broad normalized rhythm and conservative geometry."}], "do_not_invent": ["Do not invent entrances or service openings.", "Do not copy signs or tenant graphics.", "Do not claim surveyed height or exact facade spacing."], "visual_qa_cameras": visual_cameras, "web_performance_constraints": {"principle": "LOD and measured runtime cost first", "track": ["triangles", "materials", "draw_calls", "GLB_transfer_size", "runtime_nodes"], "instructions": ["reuse shared materials", "merge facade bands at runtime", "retain semantic authoring components", "use no photo textures"]}, "readiness": "RECONSTRUCTION_READY_WITH_GAPS", "generic_builder": {"material_families": sorted({base_family, accent_family}), "volumes": [], "polygon_volumes": polygon_volumes, "polygon_edge_regions": edge_regions, "facade_regions": [], "qa_cameras": qa_specs}}
    dump(package / "geometry.geojson", geometry)
    owner_centroid = shape(owner["geometry"]).centroid
    dump(package / "entity.json", {"schema_version": 1, "entity_id": asset_id, "entity_type": "BUILDING", "canonical_name": name, "status": "ACTIVE", "identity_status": "CONFIRMED", "identity_confidence": .92, "centroid": {"local_x_m": round(owner_centroid.x, 3), "local_y_m": round(owner_centroid.y, 3), "longitude": None, "latitude": None}, "geographic_feature_ids": sorted({item["properties"]["id"] for item in volumes} | {owner_id}), "source_ids": ["source:osm", *[item["source_id"] for item in reference_records]], "reconstruction_readiness": "RECONSTRUCTION_READY_WITH_GAPS"})
    dump(package / "references.json", {"schema_version": 2, "generated_at": TODAY, "records": [{**item, "source_page_url": item.pop("url"), "entity_links": [{"entity_id": asset_id, "relationship": "IDENTITY_FACTS_AND_EXTERIOR", "confidence": .9}], "reference_role": "IDENTITY_FACTS_AND_EXTERIOR", "entity_match_status": "ACCEPTED", "appearance_period": "CURRENT_OR_RECENT", "storage_status": "REMOTE_METADATA_ONLY", "viewable_for_research": True} for item in reference_records]})
    dump(package / "rights.json", {"schema_version": 2, "references": [{"reference_id": item["reference_id"], "rights_status": "RESEARCH_ONLY", "local_copy_allowed": False, "derivative_use_allowed": False, "redistribution_allowed": False, "notes": "Used only for observation; no media copied."} for item in reference_records]})
    dump(package / "observations.json", {"schema_version": 2, "observations": observations, "conflicts": []})
    coverage_aspects = {key: {"rating": "GOOD" if key in {"identity", "height", "overall_massing", "major_facades"} else "PARTIAL" if key == "materials" else "WEAK", "reference_ids": ref_ids if key not in {"height", "roof", "entrances"} else []} for key in ("identity", "height", "overall_massing", "major_facades", "roof", "materials", "entrances")}
    dump(package / "coverage.json", {"schema_version": 2, "entity_id": asset_id, "accepted_visual_reference_ids": ref_ids, "reusable_visual_reference_ids": [], "research_only_visual_reference_ids": ref_ids, "aspects": coverage_aspects, "reconstruction_readiness": "RECONSTRUCTION_READY_WITH_GAPS", "readiness_reason": "Identity, grounded polygon massing, major visible character, and broad materials are supported; exact entrances, roof plant, and weak sides stay conservative."})
    dump(package / "massing.json", {"schema_version": 1, "entity_id": asset_id, "coordinate_frame": {"axes": {"x": "east", "y": "north", "z": "up"}, "units": "metres"}, "known_dimensions": {**dims, "maximum_height_m": maximum_height, "height_status": primary["properties"].get("height_status", "UNKNOWN")}, "components": polygon_volumes, "massing_summary": f"Evidence-bounded {archetype.lower().replace('_', ' ')} using grounded source volumes."})
    dump(package / "facades.json", {"schema_version": 1, "entity_id": asset_id, "facades": [{"facade_id": f"{asset_id}:facade:perimeter", "orientation": "PERIMETER", "major_segments": ["Strong visible sides receive broad facade rhythm; weak sides remain conservative."], "floor_alignment": "APPROXIMATE_VISIBLE_RHYTHM", "bay_count": "APPROXIMATE", "opening_pattern": "normalized edge-local bands", "material_regions": ["mat:primary", "mat:accent"], "entrances": [], "setbacks": ["mapped outline and parts only"], "confidence": .65, "status": "INFERRED", "evidence_ids": ref_ids, "coverage_rating": "PARTIAL"}]})
    dump(package / "entrances.json", {"schema_version": 1, "entity_id": asset_id, "entrances": [], "status": "UNKNOWN_OMITTED"})
    dump(package / "materials.json", {"schema_version": 1, "entity_id": asset_id, "materials": [{"material_id": "mat:primary", "family": base_family, "shared_family": base_family, "status": "INFERRED", "confidence": .65, "evidence_ids": ref_ids, "exact_colour": "UNKNOWN"}, {"material_id": "mat:accent", "family": accent_family, "shared_family": accent_family, "status": "INFERRED", "confidence": .65, "evidence_ids": ref_ids, "exact_colour": "UNKNOWN"}]})
    dump(package / "evidence_gaps.json", {"schema_version": 2, "entity_id": asset_id, "aspects": {key: {"rating": value["rating"], "reference_ids": value["reference_ids"], "confidence": .7 if value["rating"] == "GOOD" else .45, "blocking": False} for key, value in coverage_aspects.items()}, "reconstruction_gate": "RECONSTRUCTION_READY_WITH_GAPS"})
    dump(package / "unknowns.json", {"schema_version": 2, "unknowns": [{"unknown_id": f"unknown:{asset_id}:entrances", "entity_id": asset_id, "description": "Exact entrance and service opening geometry", "impact": "LOD1_DETAIL", "disposition": "Omit rather than invent"}, {"unknown_id": f"unknown:{asset_id}:roof", "entity_id": asset_id, "description": "Fine rooftop equipment and weak-side modules", "impact": "LOD1_DETAIL", "disposition": "Use conservative silhouette"}]})
    dump(package / "timeline.json", {"schema_version": 1, "entity_id": asset_id, "events": [{"period": "2025-2026", "event": "Permanent architecture target state; temporary tenant graphics excluded", "status": "INFERRED", "evidence_ids": ref_ids}]})
    dump(package / "reconstruction_spec.json", spec)
    return {"entity_id": asset_id, "source_entity_id": owner_id, "name": name, "tier": "A" if wave == "A" else "B", "wave": wave, "archetype": archetype, "selection_reason": "High pedestrian/tour visibility and identity-defining massing on or near the High Street experience.", "visibility_importance": "VERY_HIGH" if wave == "A" else "HIGH", "evidence_readiness": "READY_WITH_GAPS", "expected_complexity": complexity, "target_lod": "LOD1", "reference_count": len(refs)}


def main() -> None:
    features, source = collect_entities()
    ranking = rank(features, source)
    generated_at = datetime.now(timezone.utc).isoformat()
    dump(ROOT / "data/reports/m16-priority-ranking.json", {"schema_version": 1, "milestone": "M16", "generated_at": generated_at, "method": "whole-city existing-data-only spatial and evidence-proxy scoring", "canonical_candidates": len(features), "dimensions_scale": "0..5 (complexity is cost, not quality)", "candidates": ranking})
    recovery_report = ROOT / "data/reports/m16-selected-buildings.json"
    if recovery_report.exists() and load(recovery_report).get("recovery_policy"):
        print("M16_PREP: ranking refreshed; recovered selection/packages preserved")
        return
    selected = [package_target(target, features[target[1]], source) for target in TARGETS]
    # SOM's 136 m project height conflicts with the 114.7 m OSM envelope used by
    # the draft ACPT package. Keep the target visible in the selection audit, but
    # do not send it through another reconstruction batch until reconciled.
    for item in selected:
        if item["entity_id"] == "bgc_m17_0004":
            item["evidence_readiness"] = "NOT_READY"
    sources_path = ROOT / "data/sources/sources.json"
    sources = load(sources_path)
    known_sources = {item["source_id"] for item in sources["sources"]}
    for target in TARGETS:
        for key, title, url in target[-1]:
            source_id = f"source:m17:{key}"
            if source_id not in known_sources:
                sources["sources"].append({"source_id": source_id, "source_type": "OFFICIAL_OR_PROJECT_PAGE", "provider": title.split(" — ")[0], "title": title, "url": url, "retrieved_at": TODAY, "authority_level": "SOURCE_SPECIFIC", "usage_notes": "M17 bounded evidence pass; exterior media is research-only.", "license_information": "All rights reserved unless separately established.", "cache_policy": "Metadata and URL only"})
                known_sources.add(source_id)
    dump(sources_path, sources)
    dump(ROOT / "data/reports/m16-selected-buildings.json", {"schema_version": 1, "milestone": "M16", "generated_at": generated_at, "targets": selected, "evidence_gate": "PARTIAL", "not_ready_replaced": 0})
    dump(ROOT / "data/batches/m17-batch.json", {"schema_version": 1, "milestone": "M17", "strategy": "Wave A regression gate before Wave B", "approval_policy": "VISUAL_QA_REQUIRED", "targets": [item for item in selected if item["evidence_readiness"] != "NOT_READY"]})
    registry_path = ROOT / "data/assets/buildings.json"
    registry = load(registry_path)
    for item in selected:
        if item["entity_id"] in registry["buildings"]:
            continue
        source_ids = load(ROOT / "data/reconstruction_packages" / item["entity_id"] / "entity.json")["geographic_feature_ids"]
        registry["buildings"][item["entity_id"]] = {"entity_id": item["entity_id"], "name": item["name"], "lifecycle": {"evidence": "RECONSTRUCTION_READY_WITH_GAPS", "lod2": "AVAILABLE", "lod1": "PENDING_VISUAL_QA"}, "source_feature_ids": source_ids, "runtime_merge_groups": {}, "available_lods": {"1": {"asset": f"exports/glb/buildings/{item['entity_id']}_lod1.glb", "manifest": f"data/assets/manifests/{item['entity_id']}_lod1.json", "metrics": f"data/reports/buildings/{item['entity_id']}.json", "version": "1.0", "status": "PENDING_VISUAL_QA"}, "2": {"representation": "WHOLE_BGC_TILE", "manifest": "exports/bgc/manifest.json", "source_feature_ids": source_ids, "generator": "blender/scripts/generate_bgc_tiles.py", "version": "1", "status": "AVAILABLE"}}}
    dump(registry_path, registry)
    tiers = defaultdict(int)
    for item in ranking:
        tiers[item["tier"]] += 1
    print(f"M16_PREP PARTIAL candidates={len(features)} tier_a={tiers['A']} tier_b={tiers['B']} tier_c={tiers['C']} selected={len(selected)} evidence_ready={sum(item['evidence_readiness'] != 'NOT_READY' for item in selected)}")


if __name__ == "__main__":
    main()
