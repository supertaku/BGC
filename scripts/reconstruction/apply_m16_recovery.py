"""Apply source-audited M16R facts without regenerating existing draft assets.

Idempotent: rerunning writes the same package decisions and leaves geometry,
Blender scenes, GLBs, and the runtime registry untouched.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from evidence_gate import ASPECTS, assess


ROOT = Path(__file__).resolve().parents[2]
PACKAGES = ROOT / "data/reconstruction_packages"
ARCH_PSE = "https://handelarchitects.com/project/philippine-stock-exchange"
ARCH_SUITES = "https://www.handelarchitects.com/project/the-suites-at-one-bonifacio-high-street?pagi=residential"
ARCH_OBHS = "https://handelarchitects.com/latest/one-bonifacio-high-street-in-manila-breaks-ground"
ARCH_ACPT = "https://www.som.com/projects/arthaland-century-pacific-tower/"


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def put(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def upsert(items: list[dict], key: str, value: dict) -> None:
    for index, item in enumerate(items):
        if item.get(key) == value[key]:
            items[index] = value
            return
    items.append(value)


def aspect(rating: str, basis: str, ids: list[str] | None = None) -> dict:
    return {"rating": rating, "basis": basis, "reference_ids": ids or []}


def observation(entity: str, key: str, prop: str, value, source: str, ref: str,
                status: str = "VERIFIED_AUTHORITATIVE", confidence: float = .9) -> dict:
    return {"observation_id": f"obs:{entity}:{key}", "entity_id": entity,
            "property": prop, "value": value, "status": status,
            "confidence": confidence, "source_ids": [source], "reference_ids": [ref],
            "method": "architect_project_page", "affected_component": key,
            "notes": "Source fact; geometry interpretation still requires visual QA."}


def main() -> None:
    sources_path = ROOT / "data/sources/sources.json"
    sources = read(sources_path)
    upsert(sources["sources"], "source_id", {
        "source_id": "source:m16r:architect-pse", "source_type": "ARCHITECT_PROJECT_PAGE",
        "provider": "Handel Architects", "title": "Philippine Stock Exchange",
        "url": ARCH_PSE, "retrieved_at": "2026-09-25",
        "authority_level": "VERIFIED_AUTHORITATIVE",
        "usage_notes": "Architect project facts and research-only exterior photographs.",
        "license_information": "All rights reserved; no image redistribution.",
        "cache_policy": "Store observations and URL only",
    })
    put(sources_path, sources)

    selected_path = ROOT / "data/reports/m16-selected-buildings.json"
    selected = read(selected_path)
    selected["recovery_policy"] = "Only READY_FOR_VISUAL_RECONSTRUCTION targets may enter the final batch. Original drafts remain unpublished."
    selected["initial_targets"] = [target["entity_id"] for target in selected["targets"]]

    for target in selected["targets"]:
        entity = target["entity_id"]
        package = PACKAGES / entity
        spec_path = package / "reconstruction_spec.json"
        spec = read(spec_path)
        refs_path = package / "references.json"
        refs = read(refs_path)
        obs_path = package / "observations.json"
        obs = read(obs_path)
        height = spec["known_dimensions"]["maximum_height_m"]
        source = "source:osm"
        scope = "RESOLVED"
        view_records: list[dict] = []
        coverage = {key: aspect("NONE", "No aspect-specific review yet") for key in ASPECTS}
        coverage["identity"] = aspect("GOOD", "Named OSM entity and project identity", [])
        coverage["footprint"] = aspect("PARTIAL", "Processed OSM footprint; community mapping, not survey")
        coverage["height"] = aspect("PARTIAL" if spec["known_dimensions"]["height_status"] != "PROCEDURAL" else "WEAK",
                                      "OSM height or explicit procedural fallback")
        if entity == "bgc_m17_0001":
            scope = "UNRESOLVED"
            target["name"] = "One Bonifacio High Street — retail mall/podium candidate"
            spec["target"]["name"] = target["name"]
            coverage["identity"] = aspect("CONFLICTED", "OSM tags identify a mall; architect project name denotes whole mixed-use development")
            coverage["massing"] = aspect("WEAK", "12 m is a procedural fallback; OSM mall polygon overlaps Suites and PSE tower outlines")
            scope_report = ROOT / "data/reports/m16-obhs-scope.json"
            target["scope_note"] = "OSM shop=mall polygon includes tower ground footprints; retail component boundary requires review."
            if scope_report.exists():
                target["spatial_scope_report"] = str(scope_report.relative_to(ROOT)).replace("\\", "/")
                target["spatial_scope_review"] = read(scope_report)["overlaps"]
            target["disposition"] = "DEFER_SCOPE_AND_EVIDENCE"
        elif entity == "bgc_m17_0002":
            ref = "ref:m17:architect-suites"
            coverage["massing"] = aspect("PARTIAL", "Architect describes a gently curved tower; exact curvature needs multiview review", [ref])
            coverage["principal_facade"] = aspect("PARTIAL", "Architect describes horizontal bands and glass/masonry", [ref])
            coverage["materials"] = aspect("PARTIAL", "Architect names glass and masonry", [ref])
            coverage["entrance"] = aspect("PARTIAL", "Architect describes retail and entry spaces at street level", [ref])
            for key, prop, value in [
                ("curvature", "overall_form", "gently curved tower"),
                ("banding", "principal_facade", "strong horizontal banding"),
                ("balconies", "facade_detail", "double-height balconies in some residences"),
                ("ground", "ground_relationship", "retail and entries join a multilevel courtyard"),
                ("material", "material_families", ["glass", "masonry"]),
            ]:
                upsert(obs["observations"], "observation_id", observation(entity, key, prop, value,
                       "source:m17:architect-suites", ref))
            target["disposition"] = "DEFER_SECOND_VIEWPOINT_AND_GEOMETRY"
        elif entity == "bgc_m17_0003":
            spec["builder_strategy"] = {"mode": "LANDMARK_OVERRIDE", "module": entity,
                                        "phase": "MASSING"}
            spec["landmark_parameters"] = {"roof_slope_m": 4.0,
                                           "roof_slope_state": "INFERRED_FROM_PHOTOGRAPHIC_SILHOUETTE"}
            ref = "ref:m16r:architect-pse"
            upsert(refs["records"], "reference_id", {
                "reference_id": ref, "source_id": "source:m16r:architect-pse",
                "title": "Handel Architects — Philippine Stock Exchange", "url": ARCH_PSE,
                "source_page_url": ARCH_PSE, "rights_status": "RESEARCH_ONLY",
                "asset_embedded": False, "storage_status": "REMOTE_METADATA_ONLY",
                "viewable_for_research": True, "entity_match_status": "ACCEPTED",
                "appearance_period": "CURRENT_OR_RECENT",
                "reference_role": "ARCHITECT_FACTS_AND_EXTERIOR",
                "entity_links": [{"entity_id": entity, "relationship": "ARCHITECT_FACTS_AND_EXTERIOR", "confidence": .95}],
            })
            rights_path = package / "rights.json"
            rights = read(rights_path)
            rights_template = dict(rights["references"][0])
            rights_template.update(reference_id=ref, source_url=ARCH_PSE)
            upsert(rights["references"], "reference_id", rights_template)
            photo_refs = []
            for image_id, suffix in [("00.864.11.044a", "044a"), ("00.864.11.008a", "008a")]:
                image_ref = f"ref:m16r:architect-pse:{suffix}"
                photo_refs.append(image_ref)
                image_url = f"https://s3-us-west-2.amazonaws.com/handel-architects/images/_xSmall/{image_id}.jpg"
                upsert(refs["records"], "reference_id", {
                    "reference_id": image_ref, "source_id": "source:m16r:architect-pse",
                    "title": f"Handel PSE exterior image {image_id}", "url": image_url,
                    "source_page_url": ARCH_PSE, "rights_status": "RESEARCH_ONLY",
                    "asset_embedded": False, "storage_status": "REMOTE_METADATA_ONLY",
                    "viewable_for_research": True, "entity_match_status": "ACCEPTED",
                    "appearance_period": "CURRENT_OR_RECENT",
                    "reference_role": "EXTERIOR_VIEW_UNMATCHED",
                    "entity_links": [{"entity_id": entity, "relationship": "EXTERIOR_VIEW", "confidence": .9}],
                })
                image_rights = dict(rights_template)
                image_rights.update(reference_id=image_ref, source_url=image_url)
                upsert(rights["references"], "reference_id", image_rights)
            put(rights_path, rights)
            spec["best_reference_ids"] = [ref, *photo_refs]
            coverage["massing"] = aspect("PARTIAL", "Architect documents a 30-story glass tower and inflected frontpiece; exact volumes require photo match", [ref])
            coverage["principal_facade"] = aspect("GOOD", "Architect explicitly describes inflected glazing and deep vertical solar-control ribs", [ref])
            coverage["materials"] = aspect("PARTIAL", "Architect describes glass tower; other material hues are interpretation", [ref])
            coverage["roof"] = aspect("WEAK", "Upper silhouette visible in architect image; exact roof geometry unmeasured", [ref])
            for key, prop, value in [
                ("stories", "stories", 30),
                ("frontpiece", "principal_facade", "inflected glazed frontpiece toward main commercial avenue"),
                ("ribs", "principal_facade", "deep vertical solar-control ribs on expressed spine"),
                ("composition", "facade_composition", "asymmetric tower composition"),
            ]:
                upsert(obs["observations"], "observation_id", observation(entity, key, prop, value,
                       "source:m16r:architect-pse", ref))
            upsert(obs["observations"], "observation_id", observation(
                entity, "roof-slope", "upper_silhouette", "sloped upper edges visible; 4 m draft slope is estimated",
                "source:m16r:architect-pse", ref, status="INFERRED", confidence=.45))
            # Both views show the principal street side, one elevated and one
            # at street level. Neighboring towers support a southeast-sector
            # position, but exact coordinates and lens remain estimated.
            for image_id, suffix, side, azimuth, confidence, visible in [
                ("00.864.11.044a", "044a", "SOUTHEAST_ELEVATED", 135, .55,
                 ["ground", "podium", "principal_facade", "overall_massing"]),
                ("00.864.11.008a", "008a", "SOUTHEAST_STREET", 130, .6,
                 ["principal_facade", "roof", "podium", "overall_massing"]),
            ]:
                view_records.append({"reference_id": f"ref:m16r:architect-pse:{suffix}", "source_page": ARCH_PSE,
                                     "camera_id": f"qa:{entity}:source:{suffix}",
                                     "viewpoint_side": side, "approximate_azimuth_deg": azimuth,
                                     "kind": "ELEVATED_STREET" if suffix == "044a" else "STREET",
                                     "visible_facades": ["principal"],
                                     "visible_roof": "roof" in visible, "coverage_aspects": visible,
                                     "camera_match_confidence": confidence, "useful": True,
                                     "match_basis": "Approximate southeast sector inferred from adjacent towers; lens and position estimated.",
                                     "rights_status": "RESEARCH_ONLY"})
            target["disposition"] = "CALIBRATION_MASSING_ONLY"
        elif entity == "bgc_m17_0004":
            ref = "ref:m17:architect-som-acpt"
            height = 136.0
            source = "source:m17:architect-som-acpt"
            spec["known_dimensions"].update(maximum_height_m=136.0, height_status="VERIFIED_AUTHORITATIVE")
            spec["reconstruction_height_m"] = 136.0
            spec["reconstruction_height_source_id"] = source
            spec["reconstruction_height_reference_id"] = ref
            spec["confidence"]["height"] = .9
            for volume in spec.get("generic_builder", {}).get("polygon_volumes", []):
                if volume.get("height_m") == 114.7:
                    volume["height_m"] = 136.0
                    volume["evidence_status"] = "VERIFIED_AUTHORITATIVE"
                    volume["observation_ids"] = [f"obs:{entity}:height-architect", f"obs:{entity}:footprint"]
                    volume["evidence_ids"] = [ref]
                    volume["classification"] = "OSM footprint; SOM architectural height"
            massing_path = package / "massing.json"
            massing = read(massing_path)
            massing["known_dimensions"].update(maximum_height_m=136.0, height_status="VERIFIED_AUTHORITATIVE")
            for component in massing.get("components", []):
                if component.get("height_m") == 114.7:
                    component["height_m"] = 136.0
                    component["evidence_status"] = "VERIFIED_AUTHORITATIVE"
                    component["observation_ids"] = [f"obs:{entity}:height-architect", f"obs:{entity}:footprint"]
                    component["evidence_ids"] = [ref]
                    component["classification"] = "OSM footprint; SOM architectural height"
            put(massing_path, massing)
            coverage["height"] = aspect("CONFLICTED", "OSM 114.7 m conflicts with SOM 136 m; reconstruction decision follows SOM", [ref])
            coverage["massing"] = aspect("PARTIAL", "SOM describes glass office tower with parking podium, lobby, rooftop terrace", [ref])
            coverage["principal_facade"] = aspect("PARTIAL", "SOM describes overlapping glass and changing solar shading by height", [ref])
            coverage["roof"] = aspect("PARTIAL", "SOM documents rooftop garden terrace; detailed plant omitted", [ref])
            coverage["materials"] = aspect("PARTIAL", "SOM documents glazing; no exact color or module count", [ref])
            for key, prop, value in [
                ("stories", "stories", 32),
                ("glass", "facade_composition", "overlapping glass conceals podium parking and changes appearance with height"),
                ("roof", "roof", "garden terrace, detailed equipment unknown"),
            ]:
                upsert(obs["observations"], "observation_id", observation(entity, key, prop, value,
                       source, ref))
            old = next(item for item in obs["observations"] if item["observation_id"] == f"obs:{entity}:height")
            old["notes"] = "OSM source observation retained at 114.7 m; reconstruction uses SOM's published 136 m. Conflict remains visible."
            obs["height_decision"] = {"reconstruction_height_m": 136.0, "source_id": source,
                                      "reference_id": ref, "reason": "architect-published project height",
                                      "conflicting_observation_id": f"obs:{entity}:height"}
            target["disposition"] = "DEFER_VIEWPOINT_MATCH_AND_FACADE"
        else:
            target["disposition"] = "DEFER_ASPECT_REVIEW"

        # Legacy horizontal bands remain in old exported drafts only. New
        # package builds must start with massing and target-specific facades.
        spec["generic_builder"]["polygon_edge_regions"] = []
        spec["required_procedural_approximations"] = [{
            "feature": "unknown secondary facade and exact modules",
            "classification": "PROCEDURAL",
            "instruction": "Omit unsupported details until a source-matched visual review."}]
        facades_path = package / "facades.json"
        facades = read(facades_path)
        for facade in facades.get("facades", []):
            if facade.get("opening_pattern") == "normalized edge-local bands":
                facade["opening_pattern"] = "NOT_MODELLED_PENDING_VISUAL_RECONSTRUCTION"
                facade["major_segments"] = ["Principal composition requires source-matched reconstruction."]
                facade["status"] = "UNKNOWN"
                facade["confidence"] = 0.0
        put(facades_path, facades)
        # Legacy horizontal bands may not become an architectural claim.
        for item in obs["observations"]:
            if item.get("property") == "major_facade_rhythm" and "normalized bands" in str(item.get("value")):
                item["status"] = "PROCEDURAL"
                item["source_ids"] = []
                item["reference_ids"] = []
                item["confidence"] = 0.0
                item["notes"] = "Superseded generic draft pattern; no architectural evidence claim."
        spec["readiness"] = "RECONSTRUCTION_READY_WITH_GAPS"  # schema 1.0 structural state only
        spec["visual_reconstruction_status"] = "NOT_READY"
        spec["required_coverage_aspects"] = ["identity", "overall_massing", "major_facades"]
        # The original camera labels were inferred from footprint bounds, and
        # several falsely pointed at the same web page as distinct views.
        for camera in spec.get("visual_qa_cameras", []):
            camera.update(corresponding_reference=None, confidence=0.0,
                          match_status="DIAGNOSTIC_UNMATCHED")
        for camera in spec.get("generic_builder", {}).get("qa_cameras", []):
            camera.update(kind="DIAGNOSTIC", match="UNMATCHED", reference_ids=[])
        if entity == "bgc_m17_0003":
            center = (-413.0, 63.5)
            matched = [
                ("044a", [center[0] + 220, center[1] - 165, 45], [center[0], center[1], 65], 35, .55),
                ("008a", [center[0] + 145, center[1] - 110, 3], [center[0], center[1], 68], 30, .6),
            ]
            for suffix, position, look_at, lens, confidence in matched:
                ref_id = f"ref:m16r:architect-pse:{suffix}"
                camera_id = f"qa:{entity}:source:{suffix}"
                upsert(spec["generic_builder"]["qa_cameras"], "camera_id", {
                    "camera_id": camera_id, "kind": "EVIDENCE_MATCH", "location": position,
                    "target": look_at, "lens_mm": lens, "filename": f"qa-source-{suffix}.png",
                    "match": "APPROXIMATE", "reference_ids": [ref_id]})
                upsert(spec["visual_qa_cameras"], "camera_id", {
                    "camera_id": camera_id, "position": position, "target": look_at,
                    "fov_deg": 2 * 57.2958 * math.atan(36 / (2 * lens)),
                    "corresponding_reference": ref_id, "confidence": confidence,
                    "match_status": "APPROXIMATE"})
        put(spec_path, spec)
        put(obs_path, obs)
        put(refs_path, refs)
        coverage_path = package / "evidence_coverage.json"
        put(coverage_path, {"schema_version": 1, "entity_id": entity,
                            "entity_scope_status": scope,
                            "aspects": coverage,
                            "reconstruction_height_decision": {"height_m": height, "source_ids": [source],
                                                               "conflict_retained": entity == "bgc_m17_0004"},
                            "viewpoints": view_records,
                            "review_note": "PSE views have approximate southeast camera matches; all source images remain research-only and unstored."
                                           if entity == "bgc_m17_0003" else
                                           "No view is camera matched yet; research-only images are not stored."})
        result = assess(package)
        target["evidence_readiness"] = result["status"]
        target["readiness_reasons"] = result["reasons"]
        target["coverage_file"] = str(coverage_path.relative_to(ROOT)).replace("\\", "/")
        target["reference_count"] = len(refs["records"])
        legacy_coverage_path = package / "coverage.json"
        legacy_coverage = read(legacy_coverage_path)
        mapping = {"identity": "identity", "height": "height", "overall_massing": "massing",
                   "major_facades": "principal_facade", "roof": "roof",
                   "materials": "materials", "entrances": "entrance"}
        for old_key, new_key in mapping.items():
            legacy_coverage["aspects"][old_key] = {
                "rating": coverage[new_key]["rating"],
                "reference_ids": coverage[new_key]["reference_ids"],
                "basis": coverage[new_key]["basis"]}
        legacy_coverage["visual_reconstruction_status"] = result["status"]
        legacy_coverage["readiness_reason"] = "; ".join(result["reasons"])
        put(legacy_coverage_path, legacy_coverage)
    selected["final_selected_target_ids"] = [item["entity_id"] for item in selected["targets"]
                                            if item["evidence_readiness"] == "READY_FOR_VISUAL_RECONSTRUCTION"]
    selected["evidence_gate"] = "PASS" if selected["final_selected_target_ids"] else "RECOVERY_IN_PROGRESS"
    put(selected_path, selected)
    batch_path = ROOT / "data/batches/m17-batch.json"
    batch = read(batch_path)
    batch["targets"] = [item for item in selected["targets"]
                        if item["evidence_readiness"] == "READY_FOR_VISUAL_RECONSTRUCTION"]
    batch["deferred_target_ids"] = [item["entity_id"] for item in selected["targets"]
                                    if item["evidence_readiness"] != "READY_FOR_VISUAL_RECONSTRUCTION"]
    batch["recovery_gate"] = selected["evidence_gate"]
    put(batch_path, batch)


if __name__ == "__main__":
    main()
