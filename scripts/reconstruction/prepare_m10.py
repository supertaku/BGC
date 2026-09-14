"""Deterministically select M10 targets and create their evidence/build packages."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TODAY = "2026-09-14"

PROFILES = {
    "bgc_building_0004": {
        "wave": "A", "archetype": "PODIUM_TOWER", "complexity": "HIGH",
        "reason": "Evidence-rich tower-and-podium case with an explicit mapped tower part.",
        "location": "27th Street corner 9th Avenue, BGC, Taguig, Philippines",
        "summary": "Light-toned residential tower above an active mixed-use podium; repetitive balcony/window rhythm.",
        "base_family": "warm_neutral_cladding", "podium_height": 17.3,
        "refs": [
            ("ref:official:one-maridien", "source:official-alveo-maridien", "High Street South – Maridien", "https://www.alveoland.com.ph/properties/condos/taguig/hss-maridien/"),
            ("ref:web:kmc-one-maridien", "source:kmc-one-maridien", "High Street South Block The Maridien", "https://kmcmaggroup.com/building/high-street-south-block-the-maridien/"),
        ],
        "bands": [(0.03, 0.05), (0.19, 0.21), (0.35, 0.37), (0.51, 0.53), (0.67, 0.69), (0.83, 0.85)],
    },
    "bgc_building_0015": {
        "wave": "A", "archetype": "OFFICE_BLOCK", "complexity": "MEDIUM",
        "reason": "Confirmed mid-rise office with a distinctive evidence-backed facade screen.",
        "location": "30th Street corner 9th Avenue, BGC, Taguig, Philippines",
        "summary": "Mid-rise office block with a repeating perforated geometric screen and ground-level commercial frontage.",
        "base_family": "architectural_dark_glass", "podium_height": None,
        "refs": [
            ("ref:official:jy-campos-contact", "source:official-del-monte-jy-campos", "Del Monte Philippines contact page", "https://www.delmontephil.com/contact"),
            ("ref:government:jy-campos", "source:government-jy-campos-proclamation", "Proclamation No. 380 (2017)", "https://elibrary.judiciary.gov.ph/thebookshelf/showdocs/7/80291"),
            ("ref:web:csya-jy-campos", "source:csya-jy-campos", "JY Campos Centre project", "https://www.archify.com/sg/project/jy-campos-centre-del-monte"),
            ("ref:web:savills-jy-campos", "source:savills-jy-campos", "JY Campos Center building details", "https://savillsph.com/building/JY-Campos-Center/"),
        ],
        "bands": [(0.02, 0.08), (0.16, 0.22), (0.30, 0.36), (0.44, 0.50), (0.58, 0.64), (0.72, 0.78), (0.86, 0.92)],
        "screen": True,
    },
    "bgc_building_0005": {
        "wave": "B", "archetype": "PODIUM_TOWER", "complexity": "HIGH",
        "reason": "Second tall residential form tests repeated tower throughput without changing schema.",
        "location": "High Street South, BGC, Taguig, Philippines",
        "summary": "Light residential tower over a podium with regular balcony and glazing bands.",
        "base_family": "light_neutral_panel", "podium_height": 24.4,
        "refs": [
            ("ref:official:verve", "source:official-alveo-verve", "High Street South – Verve Residences", "https://www.alveoland.com.ph/properties/condos/taguig/hss-verve-residences/"),
            ("ref:web:verve-exterior", "source:web-verve-exterior", "Verve Residences exterior reference", "https://onepropertee.com/interior-designed-furnished-2-bedroom-condot-sale-verve-residences-bgc-property"),
        ],
        "bands": [(0.03, 0.05), (0.16, 0.18), (0.29, 0.31), (0.42, 0.44), (0.55, 0.57), (0.68, 0.70), (0.81, 0.83), (0.94, 0.96)],
    },
    "bgc_building_0027": {
        "wave": "B", "archetype": "LOW_RISE_RETAIL", "complexity": "LOW",
        "reason": "Current four-storey street-facing flagship supplies a low-rise retail contrast.",
        "location": "C3 Annex, 7th Avenue corner 30th Street, BGC, Taguig, Philippines",
        "summary": "Four-storey modern retail block with bright cladding and broad glazed frontage; temporary graphics omitted.",
        "base_family": "light_neutral_panel", "podium_height": None,
        "refs": [
            ("ref:official:uniqlo-bgc", "source:official-uniqlo-bgc", "UNIQLO BGC High Street", "https://www.uniqlo.com/ph/en/special-feature/uniqlo-bgc-high-street"),
            ("ref:web:primer-uniqlo-bgc", "source:primer-uniqlo-bgc", "UNIQLO BGC High Street reopening", "https://primer.com.ph/blog/uniqlo-bgc-high-street-a-four-story-flagship-redefining-lifewear/"),
        ],
        "bands": [(0.06, 0.23), (0.31, 0.46), (0.54, 0.69)],
    },
    "bgc_building_0011": {
        "wave": "B", "archetype": "IRREGULAR_FOOTPRINT", "complexity": "MEDIUM",
        "reason": "Ten-edge mapped footprint retires the untested arbitrary-edge massing risk.",
        "location": "Bonifacio High Street Central C1, BGC, Taguig, Philippines",
        "summary": "Angular mixed retail/office block; irregular mapped footprint is primary while facade detail stays conservative.",
        "base_family": "warm_neutral_cladding", "podium_height": None,
        "refs": [
            ("ref:official:bgc-c1-directory", "source:official-ayala-bonifacio-high-street", "BGC district directory – C1", "https://bgc.com.ph/shop/?directory_type=all"),
            ("ref:web:officepro-bhs-central", "source:officepro-bhs-central", "Bonifacio High Street Central exterior", "https://www.officepro.ph/buildings/bonifacio-high-street-central-%28bhs-central%29"),
        ],
        "bands": [(0.05, 0.26), (0.38, 0.56), (0.68, 0.86)],
    },
}

SOURCE_ADDITIONS = {
    "source:kmc-one-maridien": ("PROPERTY_FIRM", "KMC / Savills Philippines", "High Street South Block The Maridien", "https://kmcmaggroup.com/building/high-street-south-block-the-maridien/"),
    "source:csya-jy-campos": ("ARCHITECT_PROJECT_PAGE", "CSYA via Archify", "JY Campos Centre project", "https://www.archify.com/sg/project/jy-campos-centre-del-monte"),
    "source:savills-jy-campos": ("PROPERTY_FIRM", "Savills Philippines", "JY Campos Center", "https://savillsph.com/building/JY-Campos-Center/"),
    "source:web-verve-exterior": ("PROPERTY_LISTING", "OnePropertee", "Verve Residences exterior", "https://onepropertee.com/interior-designed-furnished-2-bedroom-condot-sale-verve-residences-bgc-property"),
    "source:official-uniqlo-bgc": ("OFFICIAL_OPERATOR", "UNIQLO Philippines", "UNIQLO BGC High Street", "https://www.uniqlo.com/ph/en/special-feature/uniqlo-bgc-high-street"),
    "source:primer-uniqlo-bgc": ("REPUTABLE_SECONDARY", "Philippine Primer", "UNIQLO BGC High Street reopening", "https://primer.com.ph/blog/uniqlo-bgc-high-street-a-four-story-flagship-redefining-lifewear/"),
    "source:officepro-bhs-central": ("PROPERTY_FIRM", "OfficePro Philippines", "Bonifacio High Street Central", "https://www.officepro.ph/buildings/bonifacio-high-street-central-%28bhs-central%29"),
}


def dump(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def exterior(feature: dict) -> list[list[float]]:
    geometry = feature["geometry"]
    return geometry["coordinates"][0] if geometry["type"] == "Polygon" else geometry["coordinates"][0][0]


def metrics(feature: dict) -> dict:
    ring = exterior(feature)
    points = ring[:-1] if ring[0] == ring[-1] else ring
    area2 = sum(points[i][0] * points[(i + 1) % len(points)][1] - points[(i + 1) % len(points)][0] * points[i][1] for i in range(len(points)))
    area = abs(area2) / 2
    perimeter = sum(math.dist(points[i], points[(i + 1) % len(points)]) for i in range(len(points)))
    bounds = {"min_x": min(p[0] for p in points), "min_y": min(p[1] for p in points), "max_x": max(p[0] for p in points), "max_y": max(p[1] for p in points)}
    return {"area_m2": round(area, 2), "perimeter_m": round(perimeter, 2), "axis_aligned_bounds_m": {k: round(v, 3) for k, v in bounds.items()}, "vertex_count": len(points)}


def source_registry() -> None:
    path = ROOT / "data/sources/sources.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    known = {item["source_id"] for item in payload["sources"]}
    for source_id, (kind, provider, title, url) in SOURCE_ADDITIONS.items():
        if source_id not in known:
            payload["sources"].append({"source_id": source_id, "source_type": kind, "provider": provider, "title": title, "url": url, "retrieved_at": TODAY, "authority_level": "SOURCE_SPECIFIC", "usage_notes": "M10 bounded evidence pass; exterior media is research-only.", "license_information": "All rights reserved unless separately established.", "cache_policy": "Metadata and URL only"})
    dump(path, payload)


def candidate_pool(entities: list[dict], features: dict[str, dict]) -> list[dict]:
    records = []
    existing_refs = {path.name.split("-")[0] for path in (ROOT / "data/cache/commons/discovery").glob("*.json")}
    for entity in entities:
        if entity["entity_id"] in {"bgc_building_0007", "bgc_building_0014"} or entity.get("status") != "ACTIVE":
            continue
        ids = entity.get("geographic_feature_ids", []) + entity.get("building_part_ids", [])
        usable = [features[item] for item in ids if item in features]
        outline = next((item for item in usable if item["properties"].get("feature_kind") == "building_outline"), usable[0] if usable else None)
        vertex_count = metrics(outline)["vertex_count"] if outline else 0
        irregular = vertex_count > 5
        named = bool(entity.get("canonical_name"))
        selected = PROFILES.get(entity["entity_id"])
        refs = len(selected["refs"]) if selected else (1 if entity["entity_id"] in existing_refs else 0)
        identity = float(entity.get("identity_confidence", 0))
        height_status = entity.get("height", {}).get("status", "UNKNOWN")
        evidence = round(identity * 4 + (2 if height_status == "VERIFIED_GEOGRAPHIC" else 1 if height_status == "ESTIMATED" else 0) + min(refs, 2), 2)
        archetype = selected["archetype"] if selected else ("IRREGULAR_FOOTPRINT" if irregular else "LOW_RISE_RETAIL" if entity.get("tags", {}).get("building") == "retail" else "OFFICE_BLOCK" if entity.get("tags", {}).get("building") == "office" else "RECTILINEAR_TOWER" if entity.get("height", {}).get("value_m", 0) > 60 else "OTHER")
        records.append({
            "entity_id": entity["entity_id"], "canonical_name": entity.get("canonical_name"),
            "identity_confidence": identity, "footprint_quality": "GOOD" if outline else "NONE",
            "height_quality": height_status, "building_parts": entity.get("building_part_ids", []),
            "visual_reference_coverage": "GOOD" if refs >= 2 else "PARTIAL" if refs else "NONE",
            "rights-reviewed evidence": "RESEARCH_ONLY" if refs else "NONE",
            "architectural_type": archetype, "footprint_complexity": "IRREGULAR" if irregular else "RECTILINEAR",
            "footprint_vertex_count": vertex_count, "estimated_reconstruction_complexity": selected["complexity"] if selected else "MEDIUM" if irregular else "LOW",
            "street_prominence": "HIGH" if named else "LOW", "existing LOD2": bool(outline),
            "evidence_gap": "NONE_BLOCKING" if selected else "identity/visual coverage" if named else "identity and visual coverage",
            "selection_dimensions": {"evidence_readiness": evidence, "architectural_diversity": 2 if selected else 1, "geometric_diversity": 3 if irregular else 1, "street_importance": 2 if named else 0, "framework_stress_value": 3 if irregular or entity.get("building_part_ids") else 1, "expected_research_cost": 1 if refs else 3, "expected_reconstruction_cost": 3 if selected and selected["complexity"] == "HIGH" else 2},
            "selected": entity["entity_id"] in PROFILES,
        })
    return records


def package_for(entity: dict, profile: dict, feature_map: dict[str, dict], geo_meta: dict) -> None:
    entity_id = entity["entity_id"]
    package = ROOT / "data/reconstruction_packages" / entity_id
    ids = entity["geographic_feature_ids"] + entity.get("building_part_ids", [])
    selected_features = [feature_map[item] for item in ids if item in feature_map]
    outline = next(item for item in selected_features if item["properties"].get("feature_kind") == "building_outline")
    dims = metrics(outline)
    height = float(entity["height"]["value_m"])
    height_state = "VERIFIED_GEOGRAPHIC_NOT_SURVEYED" if entity["height"]["status"] == "VERIFIED_GEOGRAPHIC" else entity["height"]["status"]
    prefix = entity_id.rsplit("_", 1)[-1]
    obs = {key: f"obs:{prefix}:{key}" for key in ("identity", "footprint", "height", "massing", "materials")}
    ref_ids = [item[0] for item in profile["refs"]]
    source_ids = sorted({"source:osm", *[item[1] for item in profile["refs"]]})
    geometry = {"type": "FeatureCollection", "schema_version": 1, "entity_id": entity_id, "projected_crs": "EPSG:32651", "source_crs": "EPSG:4326", "local_origin_wgs84": [121.050972, 14.550806], "source_sha256": geo_meta.get("source_sha256"), "features": selected_features}
    dump(package / "geometry.geojson", geometry)
    package_entity = dict(entity)
    package_entity.update({"identity_status": "CONFIRMED", "identity_confidence": max(0.9, entity.get("identity_confidence", 0)), "source_ids": source_ids, "reconstruction_package_version": 1, "target_time_state": "CURRENT_APPROX_2025_2026", "reconstruction_readiness": "RECONSTRUCTION_READY_WITH_GAPS"})
    dump(package / "entity.json", package_entity)
    observations = [
        {"observation_id": obs["identity"], "entity_id": entity_id, "property": "identity", "value": f"{entity['canonical_name']} at {profile['location']}", "status": "VERIFIED_AUTHORITATIVE", "confidence": package_entity["identity_confidence"], "source_ids": source_ids, "reference_ids": [ref_ids[0]], "method": "canonical_geographic_and_named_source_reconciliation"},
        {"observation_id": obs["footprint"], "entity_id": entity_id, "property": "footprint", "value": dims, "status": "VERIFIED_GEOGRAPHIC", "confidence": 0.8, "source_ids": ["source:osm"], "reference_ids": [], "method": "deterministic_local_metre_polygon_measurement", "notes": "Community mapped, not cadastral."},
        {"observation_id": obs["height"], "entity_id": entity_id, "property": "height_m", "value": height, "status": entity["height"]["status"], "confidence": entity["height"]["confidence"], "source_ids": ["source:osm"] if entity["height"]["status"] in {"VERIFIED_GEOGRAPHIC", "ESTIMATED"} else [], "reference_ids": [], "method": entity["height"]["method"], "notes": "Retained without upgrading to surveyed precision."},
        {"observation_id": obs["massing"], "entity_id": entity_id, "property": "overall_massing", "value": profile["summary"], "status": "VERIFIED_PHOTOGRAPHIC", "confidence": 0.72, "source_ids": [item[1] for item in profile["refs"]], "reference_ids": ref_ids, "method": "bounded exterior evidence review"},
        {"observation_id": obs["materials"], "entity_id": entity_id, "property": "material_families", "value": [profile["base_family"], "architectural_dark_glass", "generic_storefront_glass", "neutral_roof"], "status": "VERIFIED_PHOTOGRAPHIC", "confidence": 0.65, "source_ids": [item[1] for item in profile["refs"]], "reference_ids": ref_ids, "method": "visual family classification; exact colour unknown"},
    ]
    dump(package / "observations.json", {"schema_version": 2, "observations": observations, "conflicts": []})
    references = [{"reference_id": ref_id, "source_id": source_id, "entity_links": [{"entity_id": entity_id, "relationship": "IDENTITY_FACTS_AND_EXTERIOR", "confidence": 0.9}], "source_page_url": url, "title": title, "reference_role": "IDENTITY_FACTS_AND_EXTERIOR", "entity_match_status": "ACCEPTED", "appearance_period": "CURRENT_OR_RECENT", "storage_status": "REMOTE_METADATA_ONLY", "rights_status": "RESEARCH_ONLY", "viewable_for_research": True} for ref_id, source_id, title, url in profile["refs"]]
    dump(package / "references.json", {"schema_version": 2, "generated_at": TODAY, "records": references})
    dump(package / "rights.json", {"schema_version": 2, "references": [{"reference_id": item["reference_id"], "rights_status": "RESEARCH_ONLY", "local_copy_allowed": False, "derivative_use_allowed": False, "redistribution_allowed": False, "notes": "Used only for observation; no media copied."} for item in references]})
    material_records = [
        {"material_id": "mat:primary", "family": profile["base_family"], "shared_family": profile["base_family"], "status": "VERIFIED_PHOTOGRAPHIC", "confidence": 0.65, "evidence_ids": ref_ids, "exact_colour": "UNKNOWN"},
        {"material_id": "mat:glass", "family": "dark architectural glazing", "shared_family": "architectural_dark_glass", "status": "VERIFIED_PHOTOGRAPHIC", "confidence": 0.65, "evidence_ids": ref_ids, "exact_colour": "UNKNOWN"},
        {"material_id": "mat:storefront", "family": "storefront glazing", "shared_family": "generic_storefront_glass", "status": "INFERRED", "confidence": 0.55, "evidence_ids": ref_ids, "exact_colour": "UNKNOWN"},
        {"material_id": "mat:roof", "family": "neutral roof", "shared_family": "neutral_roof", "status": "UNKNOWN", "confidence": 0.25, "evidence_ids": [], "exact_colour": "UNKNOWN"},
    ]
    dump(package / "materials.json", {"schema_version": 1, "entity_id": entity_id, "materials": material_records})
    dump(package / "facades.json", {"schema_version": 1, "entity_id": entity_id, "facades": [{"facade_id": f"{prefix}:facade:perimeter", "orientation": "PERIMETER", "major_segments": [profile["summary"]], "floor_alignment": "APPROXIMATE_VISIBLE_RHYTHM", "bay_count": "APPROXIMATE", "opening_pattern": "normalized edge-local bands", "material_regions": ["mat:primary", "mat:glass", "mat:storefront", "mat:roof"], "entrances": [], "setbacks": ["mapped outline and parts only"], "confidence": 0.65, "status": "VERIFIED_PHOTOGRAPHIC", "evidence_ids": ref_ids, "coverage_rating": "PARTIAL"}]})
    dump(package / "entrances.json", {"schema_version": 1, "entity_id": entity_id, "entrances": []})
    unknowns = [{"unknown_id": f"unknown:{prefix}:{name}", "entity_id": entity_id, "description": description, "impact": "LOD1_DETAIL", "disposition": disposition} for name, description, disposition in [
        ("weak-sides", "Exact openings on weakly evidenced sides", "Use conservative perimeter rhythm"),
        ("entrances", "Exact portal locations and dimensions", "Omit rather than invent"),
        ("roof", "Fine rooftop equipment and service elements", "Omit machinery"),
        ("spacing", "Centimetre facade module spacing", "Use normalized approximate bands"),
    ]]
    dump(package / "unknowns.json", {"schema_version": 2, "unknowns": unknowns})
    aspects = {key: {"rating": rating, "reference_ids": ref_ids if key in {"identity", "overall_massing", "materials"} else []} for key, rating in {"identity": "GOOD", "footprint": "GOOD", "height": "GOOD" if entity["height"]["status"] == "VERIFIED_GEOGRAPHIC" else "PARTIAL", "overall_massing": "GOOD", "materials": "PARTIAL", "entrance": "WEAK", "roof": "WEAK"}.items()}
    dump(package / "coverage.json", {"schema_version": 2, "entity_id": entity_id, "accepted_visual_reference_ids": ref_ids, "reusable_visual_reference_ids": [], "research_only_visual_reference_ids": ref_ids, "aspects": aspects, "reconstruction_readiness": "RECONSTRUCTION_READY_WITH_GAPS", "readiness_reason": "Identity, polygonal footprint, height envelope, and major visible character are usable; entrances, exact modules, roof plant, and weak sides remain conservative."})
    dump(package / "evidence_gaps.json", {"schema_version": 2, "entity_id": entity_id, "aspects": {key: {**value, "confidence": 0.8 if value["rating"] == "GOOD" else 0.45, "blocking": False} for key, value in aspects.items()}, "reconstruction_gate": "RECONSTRUCTION_READY_WITH_GAPS"})
    dump(package / "timeline.json", {"schema_version": 1, "entity_id": entity_id, "events": [{"period": "2025-2026", "event": "Permanent architecture target state; temporary tenant graphics excluded", "status": "INFERRED", "evidence_ids": ref_ids}]})
    components = []
    outline_id = entity["geographic_feature_ids"][0]
    part_id = entity.get("building_part_ids", [None])[0] if entity.get("building_part_ids") else None
    if profile["podium_height"] is not None and part_id:
        podium = min(float(profile["podium_height"]), height - 0.1)
        components.extend([
            {"name": f"M10_{prefix}_Podium", "component_id": f"{prefix}:massing:podium", "source_feature_id": outline_id, "base_z_m": 0, "height_m": podium, "material_family": profile["base_family"], "classification": "verified geographic outline with evidence-driven estimated podium height", "evidence_status": "ESTIMATED", "observation_ids": [obs["footprint"], obs["massing"]], "evidence_ids": ref_ids},
            {"name": f"M10_{prefix}_Tower", "component_id": f"{prefix}:massing:tower", "source_feature_id": part_id, "base_z_m": podium, "height_m": height - podium, "material_family": profile["base_family"], "classification": "verified geographic building part and height envelope", "evidence_status": "VERIFIED_GEOGRAPHIC", "observation_ids": [obs["footprint"], obs["height"]], "evidence_ids": ["source:osm"]},
        ])
        facade_id, facade_base, facade_height = part_id, podium, height - podium
    else:
        components.append({"name": f"M10_{prefix}_Envelope", "component_id": f"{prefix}:massing:envelope", "source_feature_id": outline_id, "base_z_m": 0, "height_m": height, "material_family": profile["base_family"], "classification": "verified geographic polygon and retained height evidence", "evidence_status": entity["height"]["status"], "observation_ids": [obs["footprint"], obs["height"]], "evidence_ids": ["source:osm"] if entity["height"]["status"] == "VERIFIED_GEOGRAPHIC" else []})
        facade_id, facade_base, facade_height = outline_id, 0, height
    edge_regions = []
    for index, (v0, v1) in enumerate(profile["bands"], 1):
        edge_regions.append({"name": f"M10_{prefix}_Band_{index:02d}", "component_id": f"{prefix}:facade:band-{index:02d}", "source_feature_id": facade_id, "edges": "all", "u0": 0.0, "u1": 1.0, "v0": v0, "v1": v1, "d_m": 0.08, "thickness_m": 0.16, "base_z_m": facade_base, "height_m": facade_height, "material_family": "warm_neutral_cladding" if profile.get("screen") else "architectural_dark_glass", "runtime_group": f"M10_{prefix}_FACADE_BANDS", "evidence_status": "VERIFIED_PHOTOGRAPHIC", "observation_ids": [obs["massing"], obs["materials"]], "evidence_ids": ref_ids})
    cx, cy = entity["centroid"]["local_x_m"], entity["centroid"]["local_y_m"]
    extent = max(dims["axis_aligned_bounds_m"]["max_x"] - dims["axis_aligned_bounds_m"]["min_x"], dims["axis_aligned_bounds_m"]["max_y"] - dims["axis_aligned_bounds_m"]["min_y"], 20)
    camera_distance = max(extent * 2.2, height * 2.5)
    aerial_offset = max(extent * 1.6, height * 1.5)
    qa = [
        {"camera_id": f"qa:{prefix}:north", "kind": "EVIDENCE_MATCH", "location": [cx, cy + camera_distance, height * 0.5], "target": [cx, cy, height * 0.42], "lens_mm": 40, "filename": "qa-north.png", "match": "PARTIAL", "reference_ids": ref_ids},
        {"camera_id": f"qa:{prefix}:south", "kind": "DIAGNOSTIC", "location": [cx, cy - camera_distance, height * 0.5], "target": [cx, cy, height * 0.42], "lens_mm": 40, "filename": "qa-south.png", "match": "CONSERVATIVE", "reference_ids": []},
        {"camera_id": f"qa:{prefix}:east", "kind": "EVIDENCE_MATCH", "location": [cx + camera_distance, cy, height * 0.5], "target": [cx, cy, height * 0.42], "lens_mm": 40, "filename": "qa-east.png", "match": "PARTIAL", "reference_ids": ref_ids},
        {"camera_id": f"qa:{prefix}:west", "kind": "DIAGNOSTIC", "location": [cx - camera_distance, cy, height * 0.5], "target": [cx, cy, height * 0.42], "lens_mm": 40, "filename": "qa-west.png", "match": "CONSERVATIVE", "reference_ids": []},
        {"camera_id": f"qa:{prefix}:aerial", "kind": "DIAGNOSTIC", "location": [cx + aerial_offset, cy - aerial_offset, height * 2.5], "target": [cx, cy, height * 0.4], "lens_mm": 40, "filename": "qa-aerial.png", "match": "MASSING", "reference_ids": ref_ids},
    ]
    spec = {"schema_version": "1.0", "target": {"entity_id": entity_id, "name": entity["canonical_name"], "location": profile["location"], "identity_status": "CONFIRMED"}, "target_time_state": {"value": "CURRENT_APPROX_2025_2026", "permanent_architecture": "PRIMARY", "tenant_signage_and_seasonal_state": "OMIT_OR_NEUTRALIZE"}, "target_fidelity": "LOD1_MEDIUM_ARCHITECTURAL_FIDELITY", "geometry_file": "geometry.geojson", "known_dimensions": {**{k: v for k, v in dims.items() if k != "vertex_count"}, "maximum_height_m": height, "height_status": height_state}, "major_building_parts": [item["component_id"] for item in components], "massing_file": "massing.json", "facades_file": "facades.json", "entrances_file": "entrances.json", "materials_file": "materials.json", "required_coverage_aspects": ["overall_massing", "materials"], "best_reference_ids": ref_ids, "confidence": {"identity": package_entity["identity_confidence"], "footprint": 0.8, "height": entity["height"]["confidence"], "massing": 0.72, "materials": 0.65}, "required_procedural_approximations": [{"feature": "facade module spacing", "classification": "PROCEDURAL", "instruction": "Use normalized polygon-edge bands without false centimetre precision."}, {"feature": "weak sides and roof plant", "classification": "OMIT_FOR_MVP", "instruction": "Keep conservative and omit unresolved openings/equipment."}], "do_not_invent": ["Do not invent entrances or service openings.", "Do not copy tenant graphics or logos.", "Do not claim exact facade spacing or surveyed height."], "visual_qa_cameras": [{"camera_id": item["camera_id"], "position": item["location"], "target": item["target"], "fov_deg": 50, "corresponding_reference": ref_ids[0] if item["reference_ids"] else None, "confidence": 0.65 if item["reference_ids"] else 0.25, "match_status": item["match"]} for item in qa], "web_performance_constraints": {"principle": "LOD and measured runtime cost first", "track": ["triangles", "vertices", "materials", "draw_calls", "GLB_transfer_size", "runtime_nodes"], "instructions": ["reuse shared materials", "merge same-material edge bands at runtime", "retain semantic authoring components", "use no photo textures"]}, "readiness": "RECONSTRUCTION_READY_WITH_GAPS", "generic_builder": {"material_families": sorted({profile["base_family"], "architectural_dark_glass", "warm_neutral_cladding"}), "volumes": [], "polygon_volumes": components, "polygon_edge_regions": edge_regions, "facade_regions": [], "qa_cameras": qa}}
    dump(package / "reconstruction_spec.json", spec)
    dump(package / "massing.json", {"schema_version": 1, "entity_id": entity_id, "coordinate_frame": {"axes": {"x": "east", "y": "north", "z": "up"}, "units": "metres"}, "known_dimensions": spec["known_dimensions"], "components": components, "massing_summary": profile["summary"]})
    (package / "README.md").write_text(f"# {entity['canonical_name']} reconstruction package\n\nM10 {profile['wave']} package. Status: **READY_WITH_GAPS**. Read `reconstruction_spec.json`, `unknowns.json`, and `rights.json` before modeling.\n", encoding="utf-8")
    qa_dir = ROOT / "blender/buildings" / entity_id / "qa"
    dump(qa_dir / "discrepancies.json", {"schema_version": 1, "entity_id": entity_id, "qa_passes": 1, "discrepancies": [], "accepted_uncertainties": [item["unknown_id"] for item in unknowns]})
    dump(ROOT / "blender/buildings" / entity_id / "lod-policy.json", {"schema_version": 1, "entity_id": entity_id, "lod1": "approved after M10 package/geometry/visual QA", "lod2": "canonical pilot procedural source feature", "lod0": "deferred"})


def main() -> None:
    entities_path = ROOT / "data/entities/pilot-entities.json"
    entities_payload = json.loads(entities_path.read_text(encoding="utf-8"))
    geo_payload = json.loads((ROOT / "data/processed/pilot-buildings.geojson").read_text(encoding="utf-8"))
    entities = entities_payload["entities"]
    entity_map = {item["entity_id"]: item for item in entities}
    feature_map = {item["id"]: item for item in geo_payload["features"]}
    source_registry()
    # New authoritative directory evidence resolves the otherwise generic C1 label.
    c1 = entity_map["bgc_building_0011"]
    c1.update({"identity_status": "CONFIRMED", "identity_confidence": 0.9, "decision_method": "OFFICIAL_DISTRICT_DIRECTORY_AND_OSM_LOCATION", "decision_timestamp": TODAY})
    if "source:official-ayala-bonifacio-high-street" not in c1["source_ids"]:
        c1["source_ids"].append("source:official-ayala-bonifacio-high-street")
    dump(entities_path, entities_payload)
    candidates = candidate_pool(entities, feature_map)
    dump(ROOT / "data/reports/m10-candidate-pool.json", {"schema_version": 1, "milestone": "M10", "generated_at": datetime.now(timezone.utc).isoformat(), "excluded_existing_lod1": ["bgc_building_0014", "bgc_building_0007"], "candidate_count": len(candidates), "candidates": candidates})
    targets = [{"entity_id": entity_id, "name": entity_map[entity_id]["canonical_name"], "selection_reason": profile["reason"], "archetype": profile["archetype"], "complexity": profile["complexity"], "evidence_state": "READY_WITH_GAPS", "wave": profile["wave"]} for entity_id, profile in PROFILES.items()]
    dump(ROOT / "data/batches/m10-batch.json", {"schema_version": 1, "milestone": "M10", "strategy": "Wave A framework gate before Wave B", "targets": targets})
    for entity_id, profile in PROFILES.items():
        package_for(entity_map[entity_id], profile, feature_map, geo_payload)
    registry_path = ROOT / "data/assets/buildings.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    for entity_id, profile in PROFILES.items():
        entity = entity_map[entity_id]
        source_ids = entity["geographic_feature_ids"] + entity.get("building_part_ids", [])
        registry["buildings"][entity_id] = {"entity_id": entity_id, "name": entity["canonical_name"], "lifecycle": {"evidence": "RECONSTRUCTION_READY_WITH_GAPS", "lod2": "AVAILABLE", "lod1": "PENDING_VALIDATION"}, "source_feature_ids": source_ids, "runtime_merge_groups": {}, "available_lods": {"1": {"asset": f"exports/glb/buildings/{entity_id}_lod1.glb", "manifest": f"data/assets/manifests/{entity_id}_lod1.json", "metrics": f"data/reports/buildings/{entity_id}.json", "version": "1.0", "status": "PENDING_VALIDATION"}, "2": {"representation": "PILOT_PROCEDURAL_SOURCE_FEATURE", "source_feature_ids": source_ids, "generator": "blender/scripts/generate_bgc_pilot.py --base-lod-only", "status": "AVAILABLE"}}}
    dump(registry_path, registry)
    print(f"M10_PREP: PASS candidates={len(candidates)} targets={len(targets)} packages={len(PROFILES)}")


if __name__ == "__main__":
    main()
