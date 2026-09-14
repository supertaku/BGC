"""Build the M6 Central Square reconstruction package from cached evidence."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys

from pyproj import Transformer
from shapely.geometry import shape


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from evidence.model import read_json, review_rights, write_json  # noqa: E402


PACKAGE = ROOT / "data" / "reconstruction_packages" / "bgc_building_0014"
DISCOVERY = ROOT / "data" / "references" / "central-square-commons-discovery.json"
ENTITY_ID = "bgc_building_0014"
NOW = datetime.now(timezone.utc).isoformat()


def dimensions(geometry: dict) -> dict:
    polygon = shape(geometry)
    rectangle = polygon.minimum_rotated_rectangle
    corners = list(rectangle.exterior.coords)
    edges = [
        (math.dist(a, b), math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])))
        for a, b in zip(corners, corners[1:])
    ]
    lengths = sorted({round(length, 3) for length, _ in edges}, reverse=True)
    major_edge = max(edges, key=lambda item: item[0])
    east_axis_degrees = major_edge[1] % 180
    if east_axis_degrees > 90:
        east_axis_degrees -= 180
    bearing_from_north = (90 - east_axis_degrees) % 180
    min_x, min_y, max_x, max_y = polygon.bounds
    return {
        "area_m2": round(polygon.area, 2),
        "perimeter_m": round(polygon.length, 2),
        "oriented_bounding_box_m": {"major": lengths[0], "minor": lengths[1]},
        "local_axis_rotation_deg_from_east": round(east_axis_degrees, 3),
        "major_axis_bearing_deg_clockwise_from_north": round(bearing_from_north, 3),
        "axis_aligned_bounds_m": {
            "min_x": round(min_x, 3),
            "min_y": round(min_y, 3),
            "max_x": round(max_x, 3),
            "max_y": round(max_y, 3),
        },
    }


def local_camera(longitude: float, latitude: float, centroid: tuple[float, float]) -> dict:
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:32651", always_xy=True)
    origin_x, origin_y = transformer.transform(121.050972, 14.550806)
    x, y = transformer.transform(longitude, latitude)
    local_x, local_y = x - origin_x, y - origin_y
    dx, dy = centroid[0] - local_x, centroid[1] - local_y
    return {
        "wgs84": {"longitude": longitude, "latitude": latitude},
        "local_m": {"x": round(local_x, 3), "y": round(local_y, 3)},
        "camera_to_target_vector_m": {"east": round(dx, 3), "north": round(dy, 3)},
        "distance_to_centroid_m": round(math.hypot(dx, dy), 2),
        "bearing_to_target_deg_clockwise_from_north": round(math.degrees(math.atan2(dx, dy)) % 360, 2),
    }


def commons_record(page_id: str, *, role: str, directional: dict, quality: dict, appearance: str, lineage: str) -> dict:
    records = {item["page_id"]: item for item in read_json(DISCOVERY)["records"]}
    item = records[page_id]
    rights = review_rights(item.get("license_id"), item.get("license_url"), item.get("creator"))
    return {
        "reference_id": f"ref:commons:{page_id}",
        "source_id": "source:wikimedia-commons",
        "source_item_id": page_id,
        "entity_links": [{"entity_id": ENTITY_ID, "relationship": role, "confidence": quality["entity_match"]}],
        "source_page_url": item["source_page_url"],
        "asset_url": item["asset_url"],
        "thumbnail_url": item["thumbnail_url"],
        "title": item["title"],
        "description": item.get("description"),
        "creator": item.get("creator"),
        "capture_date": item.get("capture_date_raw"),
        "upload_date": item.get("upload_date"),
        "latitude": item.get("latitude"),
        "longitude": item.get("longitude"),
        "source_hash": item.get("source_hash"),
        "mime_type": item.get("mime_type"),
        "width": item.get("width"),
        "height": item.get("height"),
        "license_id": item.get("license_id"),
        "license_url": item.get("license_url"),
        "credit_line": item.get("credit_line") or item.get("creator"),
        **rights,
        "changes_disclosure_required": True if rights.get("attribution_required") else False,
        "rights_reviewed_at": NOW,
        "local_file_path": None,
        "storage_status": "REMOTE_METADATA_ONLY",
        "reference_role": role,
        "entity_match_status": "ACCEPTED",
        "appearance_period": appearance,
        "lineage_group": lineage,
        "directional_evidence": directional,
        "quality": quality,
    }


def research_record(reference_id: str, source_id: str, title: str, url: str, role: str, *,
                    capture_date: str | None = None, timestamp: str | None = None,
                    observations: list[str] | None = None, appearance: str = "UNKNOWN_DATE") -> dict:
    return {
        "reference_id": reference_id,
        "source_id": source_id,
        "source_page_url": url,
        "title": title,
        "capture_date": capture_date,
        "relevant_timestamp": timestamp,
        "reference_role": role,
        "entity_links": [{"entity_id": ENTITY_ID, "relationship": role, "confidence": 0.9}],
        "appearance_period": appearance,
        "observations": observations or [],
        "rights_status": "RESEARCH_ONLY",
        "viewable_for_research": True,
        "local_copy_allowed": False,
        "derivative_use_allowed": False,
        "commercial_use_allowed": None,
        "redistribution_allowed": False,
        "attribution_required": None,
        "share_alike_required": None,
        "changes_disclosure_required": None,
        "rights_notes": "Store URL, timestamps, and factual/visual observations only; media is not approved for bundling or texture derivation.",
        "local_file_path": None,
        "storage_status": "REMOTE_METADATA_ONLY",
    }


def gap(status: str, evidence: list[str], confidence: float, importance: str, required: bool) -> dict:
    return {
        "status": status,
        "evidence_count": len(evidence),
        "best_source": evidence[0] if evidence else None,
        "confidence": confidence,
        "importance_for_reconstruction": importance,
        "research_required": required,
    }


def main() -> None:
    geometry = read_json(PACKAGE / "geometry.geojson")
    entity = read_json(PACKAGE / "entity.json")
    outline = geometry["features"][0]
    polygon = shape(outline["geometry"])
    centroid = (polygon.centroid.x, polygon.centroid.y)
    footprint = dimensions(outline["geometry"])
    part_metrics = {
        feature["id"]: dimensions(feature["geometry"])
        for feature in geometry["features"][1:]
    }

    camera_pse = local_camera(121.047313, 14.55112, centroid)
    camera_mazda = local_camera(121.048147, 14.551833, centroid)

    references = [
        commons_record(
            "133250280",
            role="NORTH_30TH_FACADE",
            appearance="RECENT_2023",
            lineage="commons:ralff:2023-06-18-central-square",
            directional={
                "camera_position": None,
                "camera_distance_m": None,
                "camera_heading": {"value": "TOWARD_SOUTHWEST", "status": "INFERRED"},
                "viewpoint_side": "NORTHEAST",
                "viewpoint_side_status": "INFERRED_FROM_STREET_NAME_AND_VISUAL",
                "facades_visible": ["NORTH_30TH", "EAST_OTHER"],
                "primary_facade": "NORTH_30TH",
                "target_visibility": "HIGH",
                "occlusion": "LOW_TO_MODERATE",
                "perspective_quality": "GOOD_OBLIQUE",
                "camera_match_feasibility": "PARTIAL",
                "confidence": 0.82,
            },
            quality={
                "resolution": 0.95,
                "distance": 0.8,
                "target_visibility": 0.9,
                "occlusion": 0.75,
                "perspective": 0.78,
                "capture_recency": 0.72,
                "lighting": 0.9,
                "architectural_coverage": 0.86,
                "directional_confidence": 0.82,
                "rights": 1.0,
                "entity_match": 0.98,
                "overall_rank": 0.86,
            },
        ),
        commons_record(
            "40678045",
            role="INTERIOR_ATRIUM",
            appearance="HISTORICAL_2015",
            lineage="commons:holav:2015-06-02-central-square",
            directional={
                "camera_position": None,
                "viewpoint_side": "INTERIOR",
                "viewpoint_side_status": "VERIFIED_PHOTOGRAPHIC",
                "facades_visible": [],
                "primary_facade": None,
                "target_visibility": "INTERIOR_ONLY",
                "occlusion": "LOW",
                "perspective_quality": "PANORAMIC_INTERIOR",
                "camera_match_feasibility": "NOT_POSSIBLE_FOR_EXTERIOR",
                "confidence": 0.99,
            },
            quality={
                "resolution": 1.0,
                "distance": 0.9,
                "target_visibility": 0.95,
                "occlusion": 0.9,
                "perspective": 0.7,
                "capture_recency": 0.2,
                "lighting": 0.85,
                "architectural_coverage": 0.35,
                "directional_confidence": 1.0,
                "rights": 1.0,
                "entity_match": 0.98,
                "overall_rank": 0.55,
            },
        ),
        commons_record(
            "146482138",
            role="WEST_5TH_PEDESTRIAN_INTERFACE",
            appearance="RECENT_2024",
            lineage="commons:ethan-llamas:2024-03-16-bgc-auto-event",
            directional={
                "camera_position": camera_mazda,
                "camera_distance_m": camera_mazda["distance_to_centroid_m"],
                "camera_heading": {"value": camera_mazda["bearing_to_target_deg_clockwise_from_north"], "status": "INFERRED_CAMERA_TO_TARGET"},
                "viewpoint_side": "SOUTHWEST",
                "viewpoint_side_status": "VERIFIED_CAMERA_POSITION",
                "facades_visible": ["WEST_5TH", "SOUTH_HIGH_STREET"],
                "primary_facade": "WEST_5TH",
                "target_visibility": "LOW",
                "occlusion": "HIGH_FOREGROUND_VEHICLE",
                "perspective_quality": "WEAK_CLOSE_CONTEXT",
                "camera_match_feasibility": "NOT_POSSIBLE",
                "confidence": 0.74,
            },
            quality={
                "resolution": 1.0,
                "distance": 0.95,
                "target_visibility": 0.25,
                "occlusion": 0.15,
                "perspective": 0.45,
                "capture_recency": 0.82,
                "lighting": 0.55,
                "architectural_coverage": 0.28,
                "directional_confidence": 0.92,
                "rights": 1.0,
                "entity_match": 0.82,
                "overall_rank": 0.54,
            },
        ),
        commons_record(
            "158404929",
            role="SOUTH_HIGH_STREET_FACADE_CONTEXT",
            appearance="CURRENT_2025",
            lineage="commons:ph0447:2025-01-08-bhs-central",
            directional={
                "camera_position": None,
                "camera_distance_m": None,
                "camera_heading": {"value": "TOWARD_NORTHWEST", "status": "INFERRED"},
                "viewpoint_side": "SOUTHEAST",
                "viewpoint_side_status": "INFERRED_FROM_VISIBLE_BHS_LAYOUT",
                "facades_visible": ["SOUTH_HIGH_STREET", "EAST_OTHER"],
                "primary_facade": "SOUTH_HIGH_STREET",
                "target_visibility": "MODERATE",
                "occlusion": "MODERATE_TO_HIGH_VEGETATION",
                "perspective_quality": "GOOD_CONTEXT_OBLIQUE",
                "camera_match_feasibility": "PARTIAL",
                "confidence": 0.78,
            },
            quality={
                "resolution": 0.68,
                "distance": 0.68,
                "target_visibility": 0.62,
                "occlusion": 0.45,
                "perspective": 0.72,
                "capture_recency": 0.95,
                "lighting": 0.85,
                "architectural_coverage": 0.7,
                "directional_confidence": 0.78,
                "rights": 1.0,
                "entity_match": 0.93,
                "overall_rank": 0.74,
            },
        ),
        commons_record(
            "158404930",
            role="SOUTH_HIGH_STREET_STREET_CONTEXT",
            appearance="CURRENT_2025",
            lineage="commons:ph0447:2025-01-22-bhs-central",
            directional={
                "camera_position": None,
                "camera_distance_m": None,
                "camera_heading": {"value": "TOWARD_SOUTHWEST", "status": "INFERRED"},
                "viewpoint_side": "SOUTHEAST",
                "viewpoint_side_status": "INFERRED_FROM_VISIBLE_BHS_LAYOUT",
                "facades_visible": ["SOUTH_HIGH_STREET"],
                "primary_facade": "SOUTH_HIGH_STREET",
                "target_visibility": "LOW_TO_MODERATE",
                "occlusion": "HIGH_VEGETATION_AND_ADJACENT_STRUCTURE",
                "perspective_quality": "CONTEXT_ONLY",
                "camera_match_feasibility": "NOT_POSSIBLE",
                "confidence": 0.7,
            },
            quality={
                "resolution": 0.68,
                "distance": 0.55,
                "target_visibility": 0.42,
                "occlusion": 0.3,
                "perspective": 0.62,
                "capture_recency": 0.95,
                "lighting": 0.82,
                "architectural_coverage": 0.45,
                "directional_confidence": 0.7,
                "rights": 1.0,
                "entity_match": 0.88,
                "overall_rank": 0.62,
            },
        ),
        commons_record(
            "173664145",
            role="WEST_5TH_FACADE_AND_ROOFLINE",
            appearance="CURRENT_2025",
            lineage="commons:ralff:2025-08-26-pse-tower-session",
            directional={
                "camera_position": None,
                "camera_distance_m": None,
                "camera_heading": {"value": "ALONG_5TH_AVENUE_NORTHWARD", "status": "INFERRED"},
                "viewpoint_side": "SOUTHWEST_HIGH_VIEW",
                "viewpoint_side_status": "INFERRED_FROM_STREET_GEOMETRY_AND_VISUAL",
                "facades_visible": ["WEST_5TH", "SOUTH_HIGH_STREET", "ROOF"],
                "primary_facade": "WEST_5TH",
                "target_visibility": "PARTIAL",
                "occlusion": "LOW_FOR_UPPER_VOLUME_HIGH_FOR_GROUND_LEVEL",
                "perspective_quality": "HIGH_OBLIQUE",
                "camera_match_feasibility": "PARTIAL",
                "confidence": 0.78,
            },
            quality={
                "resolution": 0.9,
                "distance": 0.6,
                "target_visibility": 0.62,
                "occlusion": 0.65,
                "perspective": 0.78,
                "capture_recency": 0.98,
                "lighting": 0.8,
                "architectural_coverage": 0.68,
                "directional_confidence": 0.78,
                "rights": 1.0,
                "entity_match": 0.9,
                "overall_rank": 0.76,
            },
        ),
        commons_record(
            "173664147",
            role="AERIAL_ROOF_AND_CONTEXT",
            appearance="CURRENT_2025",
            lineage="commons:ralff:2025-08-26-pse-tower-session",
            directional={
                "camera_position": camera_pse,
                "camera_distance_m": camera_pse["distance_to_centroid_m"],
                "camera_heading": {"value": camera_pse["bearing_to_target_deg_clockwise_from_north"], "status": "INFERRED_CAMERA_TO_TARGET"},
                "viewpoint_side": "SOUTHWEST_HIGH_VIEW",
                "viewpoint_side_status": "VERIFIED_CAMERA_POSITION",
                "facades_visible": ["ROOF", "SOUTH_HIGH_STREET", "WEST_5TH"],
                "primary_facade": "ROOF",
                "target_visibility": "PARTIAL",
                "occlusion": "LOW_FOR_ROOF",
                "perspective_quality": "GOOD_AERIAL_CONTEXT",
                "camera_match_feasibility": "CAMERA_MATCH_READY",
                "confidence": 0.92,
            },
            quality={
                "resolution": 0.95,
                "distance": 0.62,
                "target_visibility": 0.7,
                "occlusion": 0.88,
                "perspective": 0.85,
                "capture_recency": 0.98,
                "lighting": 0.75,
                "architectural_coverage": 0.78,
                "directional_confidence": 0.95,
                "rights": 1.0,
                "entity_match": 0.92,
                "overall_rank": 0.84,
            },
        ),
        research_record(
            "ref:official:central-square", "source:official-ssi-central-square", "Central Square", "https://ssilife.com.ph/central-square", "AUTHORITATIVE_FACTS_AND_OFFICIAL_EXTERIOR",
            observations=["Identity, address, June 2014 opening, three retail floors, two basements, and one cinema floor.", "Official exterior image shows the northwest corner and warm neutral opaque cladding; imagery is research-only."],
            appearance="CURRENT_PAGE_UNKNOWN_CAPTURE_DATE",
        ),
        research_record(
            "ref:official:ssi-annual-report-2015", "source:official-ssi-annual-report-2015", "SSI Group, Inc. Annual Report 2015", "https://www.ssigroup.com.ph/s/Annual-Report-December-2015.pdf", "AUTHORITATIVE_FACTS",
            capture_date="2015", observations=["33,813 m2 GFA; SSI-owned retail property on FBDC land; uppermost floor transferred to Ayala Land for its cineplex."], appearance="HISTORICAL_2015",
        ),
        research_record(
            "ref:consultant:campbell-central-square", "source:consultant-campbell-central-square", "Rustan's Central Square", "https://campbell.com.ph/project/rustans-central-square/", "PROJECT_FACTS",
            observations=["Project portfolio describes four storeys, two basements, and approximately 34,000 m2."],
        ),
        research_record(
            "ref:official:ayala-cinemas-central-square", "source:official-ayala-cinemas-central-square", "Bonifacio High Street Cinemas", "https://www.ayalaallaccess.com/sites/Bonifacio-High-Street/1012", "DIRECTORY_FACT",
            observations=["Current directory page labels the cinema as Level 3; this is a marketing/directory label, not a geometric storey measurement."], appearance="CURRENT_2026",
        ),
        research_record(
            "ref:news:philstar-central-square-2014", "source:philstar-central-square-2014", "SSI Group opens Central Square BGC", "https://www.philstar.com/business/2014/10/08/1377600/ssi-group-opens-central-square-bgc", "CONTEMPORANEOUS_FACT",
            capture_date="2014-10-08", observations=["Contemporaneous report calls the mall a four-level retail destination."], appearance="HISTORICAL_2014",
        ),
        research_record(
            "ref:web:inside-metro-central-square-2024", "source:inside-the-metro-central-square-2024", "Wooshi Rolls into the Philippines", "https://www.insidethemetroph.com/food/wooshi-rolls-into-the-philippines-a-new-concept-powered-by-saladstopnbsp", "NORTHWEST_CORNER_VISUAL",
            capture_date="2024", observations=["Northwest corner shows a large digital/signage display below the permanent Central Square logo and warm neutral cladding."], appearance="RECENT_2024",
        ),
        research_record(
            "ref:youtube:tour-from-home-central-square-2021", "source:youtube-tour-from-home-central-square-2021", "Central Square Mall walking tour", "https://www.youtube.com/watch?v=rH0mV7GAa8A", "ENTRANCE_ROUTE_VIDEO",
            capture_date="2021-09", timestamp="00:06-02:17", observations=["Sequence starts on 5th Avenue and reaches the Ground Floor; supports a public approach on the west/5th Avenue side but not a precise portal survey."], appearance="HISTORICAL_2021",
        ),
        research_record(
            "ref:youtube:hg-central-square-2023", "source:youtube-hg-virtual-central-square-2023", "Tour Inside Central Square Mall at 5th Avenue BGC 2023", "https://www.youtube.com/watch?v=EE6lHwYmkl0", "EXTERIOR_AND_ENTRANCE_VIDEO",
            capture_date="2023", timestamp="OPENING_EXTERIOR_AND_ENTRY_PROGRESSION", observations=["Exterior thumbnail and opening progression show the northwest corner, ground-floor retail line, vertical glazed bay, and 5th Avenue approach."], appearance="RECENT_2023",
        ),
        research_record(
            "ref:web:urban-roamer-bhs-central-2022", "source:urban-roamer-bhs-central-2022", "The Heart of Bonifacio Global City - Part 2", "https://www.theurbanroamer.com/the-heart-of-bonifacio-global-city-part-2/", "STREET_CONTEXT_VISUAL",
            capture_date="2022", observations=["Street-context imagery and secondary description identify a four-storey box-like mall at the northwest end of BHS Central."], appearance="RECENT_2022",
        ),
        research_record(
            "ref:web:eatsplorations-shake-shack-2019", "source:eatsplorations-shake-shack-2019", "First Bite of Shake Shack Philippines - Central Square", "https://eatsplorations.com/2019/04/29/first-bite-of-shake-shack-philippines-central-square-bgc/", "GROUND_INTERFACE_VISUAL",
            capture_date="2019-04", observations=["Article distinguishes a park-facing side from a mall-lobby-facing side at the Shake Shack tenant; tenant condition is historical."], appearance="HISTORICAL_2019",
        ),
    ]

    reference_ids = {item["reference_id"] for item in references}

    observations = [
        {"observation_id": "obs:csq:identity", "entity_id": ENTITY_ID, "property": "identity", "value": "Central Square, Bonifacio High Street Central", "status": "VERIFIED_AUTHORITATIVE", "confidence": 0.99, "source_ids": ["source:official-ssi-central-square", "source:osm"], "reference_ids": ["ref:official:central-square"], "method": "official_operator_and_geographic_match", "notes": "Canonical identity remains confirmed."},
        {"observation_id": "obs:csq:address", "entity_id": ENTITY_ID, "property": "address", "value": "5th Avenue, Bonifacio High Street Central, BGC, Taguig", "status": "VERIFIED_AUTHORITATIVE", "confidence": 0.98, "source_ids": ["source:official-ssi-central-square", "source:osm"], "reference_ids": ["ref:official:central-square"], "method": "official_operator_page", "notes": None},
        {"observation_id": "obs:csq:opened", "entity_id": ENTITY_ID, "property": "opening_date", "value": "2014-06", "status": "VERIFIED_AUTHORITATIVE", "confidence": 0.97, "source_ids": ["source:official-ssi-central-square"], "reference_ids": ["ref:official:central-square"], "method": "official_operator_page", "notes": None},
        {"observation_id": "obs:csq:footprint-area", "entity_id": ENTITY_ID, "property": "footprint_area_m2", "value": footprint["area_m2"], "status": "VERIFIED_GEOGRAPHIC", "confidence": 0.8, "source_ids": ["source:osm"], "reference_ids": [], "method": "shapely_area_of_local_metre_osm_polygon", "notes": "Source is community-mapped OSM geometry, not a cadastral survey."},
        {"observation_id": "obs:csq:footprint-dimensions", "entity_id": ENTITY_ID, "property": "oriented_footprint_dimensions_m", "value": footprint["oriented_bounding_box_m"], "status": "VERIFIED_GEOGRAPHIC", "confidence": 0.8, "source_ids": ["source:osm"], "reference_ids": [], "method": "minimum_rotated_rectangle", "notes": "Dimensions are deterministic measures of the mapped footprint."},
        {"observation_id": "obs:csq:orientation", "entity_id": ENTITY_ID, "property": "major_axis_bearing_deg_clockwise_from_north", "value": footprint["major_axis_bearing_deg_clockwise_from_north"], "status": "VERIFIED_GEOGRAPHIC", "confidence": 0.8, "source_ids": ["source:osm"], "reference_ids": [], "method": "minimum_rotated_rectangle", "notes": "Undirected major axis; target-local facades are mapped separately to streets."},
        {"observation_id": "obs:csq:height", "entity_id": ENTITY_ID, "property": "height_m", "value": 25.9, "status": "VERIFIED_GEOGRAPHIC", "confidence": 0.75, "source_ids": ["source:osm"], "reference_ids": [], "method": "OSM way 470203066 explicit height tag", "notes": "Tag version 5, timestamp 2026-04-09; explicit mapped value, not an authoritative survey. No independent measured-height source found."},
        {"observation_id": "obs:csq:height-audit", "entity_id": ENTITY_ID, "property": "height_evidence_audit", "value": {"source_feature": "osm:way:470203066", "original_value": "25.9", "unit": "m", "source_timestamp": "2026-04-09T05:32:36Z", "source_version": 5, "strength": "EXPLICIT_COMMUNITY_GEOGRAPHIC_NOT_SURVEYED"}, "status": "VERIFIED_GEOGRAPHIC", "confidence": 0.75, "source_ids": ["source:osm"], "reference_ids": [], "method": "raw_osm_tag_audit", "notes": "Value retained unchanged."},
        {"observation_id": "obs:csq:official-floor-organization", "entity_id": ENTITY_ID, "property": "official_floor_organization", "value": {"retail_floors": 3, "basement_floors": 2, "cinema_floor": 1}, "status": "VERIFIED_AUTHORITATIVE", "confidence": 0.97, "source_ids": ["source:official-ssi-central-square"], "reference_ids": ["ref:official:central-square"], "method": "official_operator_page", "notes": "These are property/marketing categories, not a direct geometric storey count."},
        {"observation_id": "obs:csq:cinema-directory-label", "entity_id": ENTITY_ID, "property": "cinema_directory_label", "value": "Level 3", "status": "VERIFIED_AUTHORITATIVE", "confidence": 0.95, "source_ids": ["source:official-ayala-cinemas-central-square"], "reference_ids": ["ref:official:ayala-cinemas-central-square"], "method": "official_operator_directory", "notes": "Directory terminology only; do not translate this label into a physical storey count."},
        {"observation_id": "obs:csq:above-ground-storeys", "entity_id": ENTITY_ID, "property": "above_ground_physical_storeys", "value": {"project_consultant": 4, "contemporaneous_retail_levels": 4, "osm_building_levels": 5}, "status": "CONFLICTED", "confidence": 0.7, "source_ids": ["source:consultant-campbell-central-square", "source:philstar-central-square-2014", "source:osm"], "reference_ids": ["ref:consultant:campbell-central-square", "ref:news:philstar-central-square-2014"], "method": "cross_source_terminology_audit", "notes": "Do not force marketing/directory labels onto geometric storeys. Model vertical bands from photographic evidence and retain 25.9 m total height."},
        {"observation_id": "obs:csq:gfa", "entity_id": ENTITY_ID, "property": "gross_floor_area_m2", "value": 33813, "status": "VERIFIED_AUTHORITATIVE", "confidence": 0.98, "source_ids": ["source:official-ssi-annual-report-2015"], "reference_ids": ["ref:official:ssi-annual-report-2015"], "method": "official_annual_report", "notes": "Consultant portfolio independently rounds project area to 34,000 m2."},
        {"observation_id": "obs:csq:floor-ownership", "entity_id": ENTITY_ID, "property": "uppermost_floor_relationship", "value": "SSI transferred ownership of the uppermost floor to Ayala Land for an Ayala-operated cineplex", "status": "VERIFIED_AUTHORITATIVE", "confidence": 0.96, "source_ids": ["source:official-ssi-annual-report-2015"], "reference_ids": ["ref:official:ssi-annual-report-2015"], "method": "official_annual_report", "notes": "Functional/ownership evidence; it does not by itself define a separately expressed exterior volume."},
        {"observation_id": "obs:csq:local-sides", "entity_id": ENTITY_ID, "property": "target_local_side_mapping", "value": {"north": "30th Street", "west": "5th Avenue", "south": "Bonifacio High Street / BHS Central pedestrian corridor", "east": "adjacent-building/service side"}, "status": "VERIFIED_GEOGRAPHIC", "confidence": 0.95, "source_ids": ["source:osm"], "reference_ids": [], "method": "nearest_feature_relationship_in_existing_local_crs", "notes": "Cardinal labels are target-local convenience; the footprint is rotated about 17.6 degrees from east-west."},
        {"observation_id": "obs:csq:dominant-massing", "entity_id": ENTITY_ID, "property": "overall_massing", "value": "Broad, low-rise, predominantly box-like retail/cinema volume with an irregular footprint, flat roof/parapet, facade recesses, and ground-level setbacks", "status": "VERIFIED_PHOTOGRAPHIC", "confidence": 0.9, "source_ids": ["source:wikimedia-commons", "source:osm"], "reference_ids": ["ref:commons:133250280", "ref:commons:158404929", "ref:commons:173664145", "ref:commons:173664147"], "method": "cross_source_visual_and_geographic", "notes": "No evidence supports a distinct tall rooftop mechanical mass."},
        {"observation_id": "obs:csq:north-facade", "entity_id": ENTITY_ID, "property": "north_30th_facade", "value": "Mostly opaque warm-neutral panelled upper wall, large dark vertical glazed/recessed zones, a recessed transparent ground-floor retail line, and large mutable signage/mural zones", "status": "VERIFIED_PHOTOGRAPHIC", "confidence": 0.88, "source_ids": ["source:wikimedia-commons", "source:inside-the-metro-central-square-2024"], "reference_ids": ["ref:commons:133250280", "ref:web:inside-metro-central-square-2024"], "method": "multiple_visual_references", "notes": "Treat advertising, murals, and tenant graphics as temporary state."},
        {"observation_id": "obs:csq:south-facade", "entity_id": ENTITY_ID, "property": "south_high_street_facade", "value": "Opaque warm-neutral upper mass broken by a tall dark glazed/recessed strip; ground level is set back behind columns/storefront glazing and heavily screened by mature landscape", "status": "VERIFIED_PHOTOGRAPHIC", "confidence": 0.8, "source_ids": ["source:wikimedia-commons"], "reference_ids": ["ref:commons:158404929", "ref:commons:158404930"], "method": "two_recent_context_views", "notes": "Exact bay count and ground-floor portal positions remain unknown."},
        {"observation_id": "obs:csq:west-facade", "entity_id": ENTITY_ID, "property": "west_5th_facade", "value": "Warm-neutral opaque upper planes with a tall glazed vertical bay and recessed ground-level retail frontage along a palm-lined urban edge", "status": "VERIFIED_PHOTOGRAPHIC", "confidence": 0.76, "source_ids": ["source:wikimedia-commons", "source:youtube-tour-from-home-central-square-2021", "source:youtube-hg-virtual-central-square-2023"], "reference_ids": ["ref:commons:173664145", "ref:commons:146482138", "ref:youtube:tour-from-home-central-square-2021", "ref:youtube:hg-central-square-2023"], "method": "recent_high_view_plus_research_video", "notes": "The exact main entrance portal is not clearly surveyed."},
        {"observation_id": "obs:csq:roof", "entity_id": ENTITY_ID, "property": "roof", "value": "Predominantly broad, light-coloured flat roof within a parapet; fine equipment distribution is unresolved", "status": "VERIFIED_PHOTOGRAPHIC", "confidence": 0.75, "source_ids": ["source:wikimedia-commons"], "reference_ids": ["ref:commons:173664145", "ref:commons:173664147"], "method": "recent_high_view_photography", "notes": "Model only the major roof plane/parapet for MVP; do not invent dense mechanical equipment."},
        {"observation_id": "obs:csq:public-approach", "entity_id": ENTITY_ID, "property": "public_entrance_hierarchy", "value": "A public approach exists from 5th Avenue into the Ground Floor; exact portal extent and whether it is the primary entrance are unresolved", "status": "INFERRED", "confidence": 0.68, "source_ids": ["source:youtube-tour-from-home-central-square-2021", "source:youtube-hg-virtual-central-square-2023"], "reference_ids": ["ref:youtube:tour-from-home-central-square-2021", "ref:youtube:hg-central-square-2023"], "method": "video_route_sequence", "notes": "Use an understated entrance placeholder until a facade-normal still or perimeter video closes the gap."},
        {"observation_id": "obs:csq:street-context", "entity_id": ENTITY_ID, "property": "street_context", "value": {"north": "30th Street vehicular edge with streetlights and trees", "west": "5th Avenue vehicular edge with signalized intersection and palms", "south": "BHS Central pedestrian park/corridor with mature trees, lawn/terraced steps, seating, lights, and temporary event elements", "east": "close adjacent retail mass"}, "status": "VERIFIED_PHOTOGRAPHIC", "confidence": 0.88, "source_ids": ["source:wikimedia-commons", "source:osm"], "reference_ids": ["ref:commons:133250280", "ref:commons:158404929", "ref:commons:158404930", "ref:commons:173664147"], "method": "recent_visual_and_geographic_context", "notes": "Temporary tents, vehicles, banners, and seasonal decor are not permanent architecture."},
    ]

    massing = {
        "schema_version": 1,
        "entity_id": ENTITY_ID,
        "coordinate_frame": geometry["local_frame"],
        "target_local_frame": {
            "centroid_local_m": {"x": round(centroid[0], 3), "y": round(centroid[1], 3)},
            "north_side": "30th Street",
            "west_side": "5th Avenue",
            "south_side": "Bonifacio High Street / BHS Central",
            "east_side": "adjacent-building/service side",
            "footprint_rotation_deg_from_east": footprint["local_axis_rotation_deg_from_east"],
        },
        "known_dimensions": footprint,
        "height_audit": observations[7]["value"],
        "components": [
            {"component_id": "csq:massing:envelope-outline", "geometry_basis": "osm:way:205968610", "footprint_metrics": footprint, "height_m": 25.9, "min_height_m": 5.2, "height_status": "VERIFIED_GEOGRAPHIC", "relationship_to_parent": "ROOT_OUTLINE_HORIZONTAL_CONTROL", "evidence": ["source:osm", "ref:commons:173664147"], "confidence": 0.8, "modeling_class": "REFERENCE_ONLY", "modeling_action": "DO_NOT_EXTRUDE_AS_A_UNIFORM_SOLID; build contained parts instead", "notes": "The OSM outline carries height=25.9 and min_height=5.2. Treat it as horizontal perimeter control; the contained parts define solids."},
            {"component_id": "csq:massing:main-volume", "geometry_basis": "osm:way:470203066", "footprint_metrics": part_metrics["osm:way:470203066"], "height_m": 25.9, "height_status": "VERIFIED_GEOGRAPHIC", "relationship_to_parent": "CONTAINED_MAIN_VOLUME", "evidence": ["source:osm", "ref:commons:133250280", "ref:commons:173664147"], "confidence": 0.88, "modeling_class": "PARAMETRIC", "notes": "Dominant low-rise retail/cinema mass."},
            {"component_id": "csq:massing:northwest-column", "geometry_basis": "osm:way:470203065", "footprint_metrics": part_metrics["osm:way:470203065"], "height_m": 5.2, "height_status": "VERIFIED_GEOGRAPHIC", "relationship_to_parent": "SMALL_COLUMN_PART", "evidence": ["source:osm"], "confidence": 0.75, "modeling_class": "PARAMETRIC", "notes": "Retain source shape; visual expression is partly occluded."},
            {"component_id": "csq:massing:northeast-column", "geometry_basis": "osm:way:470203067", "footprint_metrics": part_metrics["osm:way:470203067"], "height_m": 3.2, "height_status": "ESTIMATED", "relationship_to_parent": "SMALL_COLUMN_PART", "evidence": ["source:osm"], "confidence": 0.55, "modeling_class": "PARAMETRIC", "notes": "Height derives from one mapped level times 3.2 m; keep visibly approximate."},
            {"component_id": "csq:massing:roof-plane", "geometry_basis": "main_volume_top", "height_m": 25.9, "height_status": "VERIFIED_GEOGRAPHIC", "relationship_to_parent": "TOP_SURFACE", "evidence": ["ref:commons:173664145", "ref:commons:173664147"], "confidence": 0.75, "modeling_class": "PROCEDURAL", "notes": "Broad light flat roof and parapet only; equipment is UNKNOWN and omitted for MVP."},
        ],
        "massing_summary": "One dominant broad low-rise volume. Use the mapped irregular outline only as horizontal perimeter control; construct solids from the contained parts, preserve the 25.9 m maximum height, and express only photo-supported recesses/setbacks.",
    }

    facades = {
        "schema_version": 1,
        "entity_id": ENTITY_ID,
        "facades": [
            {"facade_id": "csq:facade:north-30th", "orientation": "NORTH_30TH", "major_segments": ["warm-neutral opaque upper panels", "large vertical dark glazed/recessed zones", "recessed transparent ground retail band", "mutable signage/mural fields"], "floor_alignment": "Four broad visible occupied bands are plausible but exact physical storey alignment is CONFLICTED", "bay_count": "UNKNOWN", "opening_pattern": "few large vertical openings rather than a regular window grid", "material_regions": ["mat:warm-neutral-cladding", "mat:dark-glazing", "mat:storefront-glazing", "mat:dark-metal"], "entrances": [], "setbacks": ["ground floor recessed beneath upper wall"], "confidence": 0.88, "status": "VERIFIED_PHOTOGRAPHIC", "evidence_ids": ["ref:commons:133250280", "ref:web:inside-metro-central-square-2024"], "feature_confidence": {"outline": "HIGH", "large_openings": "HIGH", "exact_bays": "LOW", "signage_2026": "LOW"}},
            {"facade_id": "csq:facade:west-5th", "orientation": "WEST_5TH", "major_segments": ["opaque warm-neutral upper planes", "tall vertical glazed bay", "recessed palm-lined ground retail interface"], "floor_alignment": "Exact mullion and slab lines are not measured", "bay_count": "UNKNOWN", "opening_pattern": "large vertical glazed cuts plus ground storefront glazing", "material_regions": ["mat:warm-neutral-cladding", "mat:light-panel", "mat:dark-glazing", "mat:storefront-glazing"], "entrances": ["csq:entrance:west-public-approach"], "setbacks": ["recessed ground frontage"], "confidence": 0.76, "status": "VERIFIED_PHOTOGRAPHIC", "evidence_ids": ["ref:commons:173664145", "ref:commons:146482138", "ref:youtube:tour-from-home-central-square-2021", "ref:youtube:hg-central-square-2023"], "feature_confidence": {"outline": "HIGH", "vertical_glazed_bay": "MEDIUM_HIGH", "main_portal": "LOW", "exact_mullions": "LOW"}},
            {"facade_id": "csq:facade:south-high-street", "orientation": "SOUTH_HIGH_STREET", "major_segments": ["warm-neutral opaque upper wall", "tall dark glazed/recessed strip", "ground colonnade/storefront edge", "landscape-screened pedestrian interface"], "floor_alignment": "Partial visibility only", "bay_count": "UNKNOWN", "opening_pattern": "large vertical glazed/recessed segment and mostly opaque wall", "material_regions": ["mat:warm-neutral-cladding", "mat:dark-glazing", "mat:storefront-glazing", "mat:dark-metal"], "entrances": [], "setbacks": ["ground frontage recessed behind columns"], "confidence": 0.8, "status": "VERIFIED_PHOTOGRAPHIC", "evidence_ids": ["ref:commons:158404929", "ref:commons:158404930"], "feature_confidence": {"upper_outline": "HIGH", "ground_interface": "MEDIUM", "portal_positions": "LOW", "tenant_signage": "LOW"}},
            {"facade_id": "csq:facade:east-other", "orientation": "EAST_OTHER", "major_segments": ["massing-only neutral treatment"], "floor_alignment": "UNKNOWN", "bay_count": "UNKNOWN", "opening_pattern": "UNKNOWN", "material_regions": ["mat:warm-neutral-cladding"], "entrances": [], "setbacks": [], "confidence": 0.25, "status": "UNKNOWN", "evidence_ids": ["ref:commons:133250280", "ref:commons:158404929"], "feature_confidence": {"overall_outline": "MEDIUM", "openings": "UNKNOWN", "service_access": "UNKNOWN", "materials": "LOW"}, "procedural_rule": "Use low-detail neutral opaque treatment. Do not invent distinctive windows, loading bays, signs, or doors."},
        ],
    }

    materials = {
        "schema_version": 1,
        "entity_id": ENTITY_ID,
        "materials": [
            {"material_id": "mat:warm-neutral-cladding", "family": "warm beige/tan opaque architectural panels", "status": "VERIFIED_PHOTOGRAPHIC", "confidence": 0.92, "evidence_ids": ["ref:commons:133250280", "ref:commons:158404929", "ref:commons:173664145"], "exact_colour": "UNKNOWN", "exact_roughness": "UNKNOWN"},
            {"material_id": "mat:light-panel", "family": "light grey/off-white opaque panel", "status": "VERIFIED_PHOTOGRAPHIC", "confidence": 0.78, "evidence_ids": ["ref:commons:133250280", "ref:commons:173664145"], "exact_colour": "UNKNOWN", "exact_roughness": "UNKNOWN"},
            {"material_id": "mat:dark-glazing", "family": "dark reflective architectural glass", "status": "VERIFIED_PHOTOGRAPHIC", "confidence": 0.9, "evidence_ids": ["ref:commons:133250280", "ref:commons:158404929", "ref:commons:173664145"], "exact_transmission": "UNKNOWN", "exact_roughness": "UNKNOWN"},
            {"material_id": "mat:storefront-glazing", "family": "clear-to-dark ground-floor storefront glazing", "status": "VERIFIED_PHOTOGRAPHIC", "confidence": 0.82, "evidence_ids": ["ref:commons:133250280", "ref:commons:146482138"], "exact_transmission": "UNKNOWN", "exact_roughness": "UNKNOWN"},
            {"material_id": "mat:dark-metal", "family": "dark metal frames/columns", "status": "VERIFIED_PHOTOGRAPHIC", "confidence": 0.78, "evidence_ids": ["ref:commons:133250280", "ref:commons:158404929"], "exact_finish": "UNKNOWN"},
            {"material_id": "mat:signage-display", "family": "digital or printed advertising/signage surface", "status": "VERIFIED_PHOTOGRAPHIC", "confidence": 0.86, "evidence_ids": ["ref:commons:133250280", "ref:web:inside-metro-central-square-2024"], "permanence": "TEMPORARY_OR_MUTABLE", "mvp_treatment": "neutral emissive/graphic placeholder without copied logos or campaigns"},
        ],
    }

    entrances = {
        "schema_version": 1,
        "entity_id": ENTITY_ID,
        "entrances": [
            {"entrance_id": "csq:entrance:west-public-approach", "type": "PUBLIC_APPROACH", "hierarchy": "PRIMARY_CANDIDATE", "side": "WEST_5TH", "position": "UNKNOWN_WITHIN_WEST_GROUND_FRONTAGE", "status": "INFERRED", "confidence": 0.68, "evidence_ids": ["ref:youtube:tour-from-home-central-square-2021", "ref:youtube:hg-central-square-2023"], "geometry_guidance": "Use a simple recessed glazed entrance placeholder aligned with the visible ground retail setback; do not claim exact width or canopy geometry."},
            {"entrance_id": "csq:entrance:south-public", "type": "PUBLIC_ENTRANCE", "hierarchy": "UNKNOWN", "side": "SOUTH_HIGH_STREET", "position": "UNKNOWN", "status": "UNKNOWN", "confidence": 0.2, "evidence_ids": ["ref:commons:158404929"], "geometry_guidance": "Do not add a distinctive portal without new evidence."},
            {"entrance_id": "csq:entrance:basement-access", "type": "VEHICULAR_OR_SERVICE", "hierarchy": "UNKNOWN", "side": "UNKNOWN", "position": "UNKNOWN", "status": "UNKNOWN", "confidence": 0.1, "evidence_ids": [], "geometry_guidance": "Omit from first reconstruction unless GIS or capture evidence resolves it."},
        ],
    }

    unknowns = {
        "schema_version": 1,
        "entity_id": ENTITY_ID,
        "unknowns": [
            {"unknown_id": "unknown:csq:east-facade", "aspect": "east/service facade", "importance": "MEDIUM", "status": "UNKNOWN", "rule": "neutral massing-only facade; no invented doors, loading bays, or signage", "closure_action": "facade-normal still from the east-side passage"},
            {"unknown_id": "unknown:csq:entrance-portals", "aspect": "exact entrance hierarchy and portal geometry", "importance": "HIGH", "status": "UNKNOWN", "rule": "use understated recessed glazed placeholder", "closure_action": "full-height stills of every public entrance with both adjacent corners"},
            {"unknown_id": "unknown:csq:roof-equipment", "aspect": "roof mechanical equipment and screening", "importance": "LOW_FOR_LOD1", "status": "UNKNOWN", "rule": "flat roof/parapet only; omit fine plant", "closure_action": "recent elevated oblique roof image"},
            {"unknown_id": "unknown:csq:storey-mapping", "aspect": "physical storeys versus directory labels", "importance": "MEDIUM", "status": "CONFLICTED", "rule": "use photo-visible broad horizontal bands within 25.9 m; do not encode directory names as geometry", "closure_action": "section drawing or facade-normal survey"},
            {"unknown_id": "unknown:csq:mullion-spacing", "aspect": "exact glazing mullion rhythm", "importance": "LOW_FOR_LOD1", "status": "ESTIMATED", "rule": "maintain approximate large-bay rhythm only", "closure_action": "facade-normal high-resolution photographs"},
            {"unknown_id": "unknown:csq:current-signage", "aspect": "2025-2026 tenant and advertising state", "importance": "LOW", "status": "UNKNOWN", "rule": "separate permanent logo zone from temporary tenant/campaign graphics; omit or simplify trademarks", "closure_action": "dated 2026 perimeter capture"},
            {"unknown_id": "unknown:csq:basement-ramp", "aspect": "basement vehicular access location", "importance": "MEDIUM", "status": "UNKNOWN", "rule": "omit until evidenced", "closure_action": "street-level perimeter capture focused on ramps/service access"},
        ],
    }

    gaps = {
        "schema_version": 1,
        "entity_id": ENTITY_ID,
        "generated_at": NOW,
        "fields": {
            "identity": gap("GOOD", ["ref:official:central-square"], 0.99, "CRITICAL", False),
            "footprint": gap("GOOD", ["source:osm"], 0.8, "CRITICAL", False),
            "building_parts": gap("GOOD", ["source:osm"], 0.8, "HIGH", False),
            "overall_height": gap("GOOD", ["source:osm"], 0.75, "CRITICAL", False),
            "above_ground_floor_organization": gap("PARTIAL_CONFLICTED", ["ref:official:central-square", "ref:consultant:campbell-central-square", "source:osm"], 0.7, "HIGH", False),
            "basement_structure": gap("PARTIAL", ["ref:official:central-square", "ref:consultant:campbell-central-square"], 0.95, "LOW_FOR_EXTERIOR", False),
            "overall_massing": gap("GOOD", ["ref:commons:133250280", "ref:commons:173664147", "source:osm"], 0.9, "CRITICAL", False),
            "north_exterior": gap("GOOD", ["ref:commons:133250280", "ref:web:inside-metro-central-square-2024"], 0.88, "HIGH", False),
            "south_exterior": gap("PARTIAL", ["ref:commons:158404929", "ref:commons:158404930"], 0.8, "HIGH", False),
            "east_exterior": gap("WEAK", ["ref:commons:133250280", "ref:commons:158404929"], 0.35, "MEDIUM", True),
            "west_exterior": gap("PARTIAL", ["ref:commons:173664145", "ref:youtube:tour-from-home-central-square-2021"], 0.76, "HIGH", False),
            "main_entrance": gap("PARTIAL", ["ref:youtube:tour-from-home-central-square-2021", "ref:youtube:hg-central-square-2023"], 0.68, "CRITICAL", True),
            "secondary_entrances": gap("UNKNOWN", [], 0.15, "MEDIUM", True),
            "30th_street_relationship": gap("GOOD", ["ref:commons:133250280", "source:osm"], 0.9, "HIGH", False),
            "5th_avenue_relationship": gap("GOOD", ["ref:commons:173664145", "ref:youtube:tour-from-home-central-square-2021", "source:osm"], 0.88, "HIGH", False),
            "bonifacio_high_street_relationship": gap("GOOD", ["ref:commons:158404929", "ref:commons:158404930", "source:osm"], 0.9, "HIGH", False),
            "podium": gap("PARTIAL", ["ref:commons:133250280", "ref:commons:158404929"], 0.72, "HIGH", False),
            "roof": gap("PARTIAL", ["ref:commons:173664147", "ref:commons:173664145"], 0.75, "MEDIUM", True),
            "facade_materials": gap("GOOD", ["ref:commons:133250280", "ref:commons:158404929", "ref:commons:173664145"], 0.9, "HIGH", False),
            "glass_treatment": gap("GOOD", ["ref:commons:133250280", "ref:commons:173664145"], 0.86, "MEDIUM", False),
            "opaque_wall_treatment": gap("GOOD", ["ref:commons:133250280", "ref:commons:158404929"], 0.9, "HIGH", False),
            "columns": gap("PARTIAL", ["source:osm", "ref:commons:158404929"], 0.68, "MEDIUM", False),
            "setbacks": gap("PARTIAL", ["ref:commons:133250280", "ref:commons:158404929"], 0.72, "HIGH", False),
            "openings": gap("PARTIAL", ["ref:commons:133250280", "ref:commons:158404929"], 0.72, "HIGH", False),
            "signage_zones": gap("GOOD_MUTABLE", ["ref:commons:133250280", "ref:web:inside-metro-central-square-2024"], 0.86, "LOW", False),
            "storefront_rhythm": gap("WEAK", ["ref:commons:146482138", "ref:commons:158404929"], 0.55, "MEDIUM", True),
            "pedestrian_interface": gap("GOOD", ["ref:commons:158404929", "ref:commons:158404930", "ref:commons:146482138"], 0.86, "HIGH", False),
            "neighboring_buildings": gap("GOOD", ["ref:commons:173664147", "ref:commons:158404929", "source:osm"], 0.9, "MEDIUM", False),
            "street_furniture": gap("GOOD", ["ref:commons:133250280", "ref:commons:158404929"], 0.84, "LOW", False),
            "vegetation": gap("GOOD", ["ref:commons:158404929", "ref:commons:158404930"], 0.92, "MEDIUM", False),
            "night_appearance": gap("WEAK", ["ref:commons:146482138"], 0.48, "LOW", True),
            "historical_current_consistency": gap("PARTIAL", ["ref:commons:133250280", "ref:commons:158404929", "ref:commons:173664145"], 0.78, "MEDIUM", False),
        },
        "research_stop_rule_result": "STOP: additional targeted searches predominantly returned duplicate, tenant, event, interior, or weakly framed material. Major geometry-producing features are sufficient for LOD1; remaining critical precision needs targeted capture or non-public drawings.",
    }

    coverage = {
        "entity_id": ENTITY_ID,
        "canonical_name": "Central Square",
        "identity": "CONFIRMED",
        "height_evidence": "VERIFIED_GEOGRAPHIC_NOT_SURVEYED",
        "target_time_state": "CURRENT_APPROX_2025_2026",
        "unique_exterior_viewpoints": 5,
        "directionally_resolved_viewpoints": 5,
        "reusable_visual_reference_ids": [item["reference_id"] for item in references if item["reference_id"].startswith("ref:commons:")],
        "research_only_visual_reference_ids": ["ref:official:central-square", "ref:web:inside-metro-central-square-2024", "ref:youtube:tour-from-home-central-square-2021", "ref:youtube:hg-central-square-2023", "ref:web:urban-roamer-bhs-central-2022", "ref:web:eatsplorations-shake-shack-2019"],
        "aspects": {
            "overall_massing": {"rating": "GOOD", "reference_ids": ["ref:commons:133250280", "ref:commons:173664147"]},
            "north_30th_side": {"rating": "GOOD", "reference_ids": ["ref:commons:133250280", "ref:web:inside-metro-central-square-2024"]},
            "west_5th_side": {"rating": "PARTIAL", "reference_ids": ["ref:commons:173664145", "ref:commons:146482138", "ref:youtube:tour-from-home-central-square-2021"]},
            "south_high_street_side": {"rating": "PARTIAL", "reference_ids": ["ref:commons:158404929", "ref:commons:158404930"]},
            "east_other_side": {"rating": "WEAK", "reference_ids": ["ref:commons:133250280", "ref:commons:158404929"]},
            "entrance": {"rating": "PARTIAL", "reference_ids": ["ref:youtube:tour-from-home-central-square-2021", "ref:youtube:hg-central-square-2023"]},
            "roof": {"rating": "PARTIAL", "reference_ids": ["ref:commons:173664145", "ref:commons:173664147"]},
            "materials": {"rating": "GOOD", "reference_ids": ["ref:commons:133250280", "ref:commons:158404929", "ref:commons:173664145"]},
            "street_context": {"rating": "GOOD", "reference_ids": ["ref:commons:133250280", "ref:commons:158404929", "ref:commons:158404930", "ref:commons:173664147"]},
        },
        "important_missing_evidence": ["facade-normal entry portal photographs", "east/service-side continuity", "fine roof equipment/screens", "basement ramp/service access"],
        "recommended_fidelity_tier": "LOD1_MEDIUM_ARCHITECTURAL_FIDELITY",
        "reconstruction_readiness": "RECONSTRUCTION_READY_WITH_GAPS",
    }

    rights = {
        "schema_version": 2,
        "policy": "VIEWABLE does not imply redistributable. Commons files are reviewed individually; all other imagery remains metadata-only research evidence.",
        "references": [
            {
                "reference_id": item["reference_id"],
                "creator": item.get("creator"),
                "license_id": item.get("license_id"),
                "license_url": item.get("license_url"),
                "attribution_text": f"{item.get('title')} — {item.get('creator')} — {item.get('license_id')} — {item.get('source_page_url')}",
                "source_url": item.get("source_page_url"),
                "rights_status": item["rights_status"],
                "attribution_required": item.get("attribution_required"),
                "share_alike_required": item.get("share_alike_required"),
                "changes_disclosure_required": item.get("changes_disclosure_required"),
                "local_copy_allowed": item.get("local_copy_allowed"),
                "derivative_use_allowed": item.get("derivative_use_allowed"),
                "redistribution_allowed": item.get("redistribution_allowed"),
                "local_file_path": None,
            }
            for item in references
        ],
    }

    timeline = {
        "schema_version": 1,
        "entity_id": ENTITY_ID,
        "recommended_target_time_state": "CURRENT_APPROX_2025_2026",
        "entries": [
            {"period": "2014-06", "event": "Central Square opened", "status": "VERIFIED_AUTHORITATIVE", "evidence_ids": ["ref:official:central-square", "ref:news:philstar-central-square-2014"]},
            {"period": "2015", "event": "Official report records 33,813 m2 GFA and the Ayala-operated uppermost cineplex floor; Commons interior records the early atrium state", "status": "VERIFIED_AUTHORITATIVE_AND_PHOTOGRAPHIC", "evidence_ids": ["ref:official:ssi-annual-report-2015", "ref:commons:40678045"]},
            {"period": "2019", "event": "Shake Shack park/lobby interface documented; tenant configuration is historical", "status": "VERIFIED_FROM_RESEARCH_VISUAL", "evidence_ids": ["ref:web:eatsplorations-shake-shack-2019"]},
            {"period": "2021-2023", "event": "5th Avenue approach, northwest corner, major cladding/glazing composition, and mural/tenant state documented", "status": "VERIFIED_FROM_VISUAL_REFERENCES", "evidence_ids": ["ref:youtube:tour-from-home-central-square-2021", "ref:commons:133250280", "ref:youtube:hg-central-square-2023"]},
            {"period": "2024", "event": "Northwest corner photographed with a large mutable digital/signage display; permanent wall/logo zone remains recognizable", "status": "VERIFIED_FROM_RESEARCH_VISUAL", "evidence_ids": ["ref:web:inside-metro-central-square-2024"]},
            {"period": "2025", "event": "Recent south/High Street, west/5th Avenue, roof, and surrounding-context views show no observed major silhouette change", "status": "INFERRED_FROM_MULTIPLE_RECENT_PHOTOS", "evidence_ids": ["ref:commons:158404929", "ref:commons:158404930", "ref:commons:173664145", "ref:commons:173664147"]},
        ],
        "source_age_distribution": {"2014": 1, "2015": 2, "2019": 1, "2021": 1, "2022": 1, "2023": 2, "2024": 2, "2025": 4, "2026_current_page_or_directory": 2, "unknown_capture_date": 0},
        "chronology_rule": "Model permanent architecture to approximately 2025-2026. Keep tenant, mural, advertising, event tents, and seasonal decor separate and optional.",
    }

    reconstruction_spec = {
        "schema_version": 1,
        "target": {"entity_id": ENTITY_ID, "name": "Central Square", "location": "Bonifacio High Street Central, BGC, Taguig, Philippines", "identity_status": "CONFIRMED"},
        "target_time_state": {"value": "CURRENT_APPROX_2025_2026", "permanent_architecture": "PRIMARY", "tenant_signage_and_seasonal_state": "OPTIONAL_SIMPLIFIED"},
        "target_fidelity": "LOD1_MEDIUM_ARCHITECTURAL_FIDELITY",
        "known_dimensions": footprint | {"maximum_height_m": 25.9, "height_status": "VERIFIED_GEOGRAPHIC_NOT_SURVEYED"},
        "major_building_parts": [item["component_id"] for item in massing["components"]],
        "massing_file": "massing.json",
        "facades_file": "facades.json",
        "entrances_file": "entrances.json",
        "materials_file": "materials.json",
        "street_relationship": next(
            item["value"] for item in observations if item["observation_id"] == "obs:csq:street-context"
        ),
        "best_reference_ids": ["ref:commons:133250280", "ref:commons:158404929", "ref:commons:173664145", "ref:commons:173664147", "ref:youtube:tour-from-home-central-square-2021"],
        "confidence": {"identity": 0.99, "footprint": 0.8, "height": 0.75, "massing": 0.9, "north_30th": 0.88, "west_5th": 0.76, "south_high_street": 0.8, "east_other": 0.25, "entrance": 0.68, "roof_major_plane": 0.75, "materials": 0.9},
        "required_procedural_approximations": [
            {"feature": "east/service facade", "classification": "PROCEDURAL", "instruction": "neutral low-detail opaque treatment"},
            {"feature": "west public entrance portal", "classification": "PARAMETRIC_PLACEHOLDER", "instruction": "simple recessed glazed portal; expose dimensions as parameters"},
            {"feature": "repeated facade panels/bays", "classification": "PROCEDURAL", "instruction": "derive approximate large-bay rhythm from evidence; avoid false fine precision"},
            {"feature": "distinctive northwest corner/signage frame", "classification": "CUSTOM", "instruction": "model the wall/display recess as geometry; keep campaign artwork neutral"},
            {"feature": "roof mechanical equipment", "classification": "OMIT_FOR_MVP", "instruction": "major flat roof/parapet only"},
            {"feature": "tiny tenant hardware and rooftop piping", "classification": "OMIT_FOR_MVP", "instruction": "omit"},
        ],
        "do_not_invent": [
            "Do not invent high-detail roof plant, pipes, or screens.",
            "Do not invent east/service-side loading bays, doors, or signage.",
            "Do not claim an exact main entrance width or hierarchy.",
            "Do not map Lower Ground/Upper Ground/Second/Third/Cinema labels directly to geometric storey indices.",
            "Do not copy research-only advertising, tenant campaigns, or trademarks into textures.",
            "Do not change the 25.9 m height without new evidence.",
            "Do not treat Commons files from one capture session as independent corroboration merely by count.",
        ],
        "future_blender_object_hierarchy": [
            "CSQ_ROOT",
            "CSQ_ROOT/MASSING/MAIN_VOLUME",
            "CSQ_ROOT/MASSING/COLUMNS",
            "CSQ_ROOT/FACADES/NORTH_30TH",
            "CSQ_ROOT/FACADES/WEST_5TH",
            "CSQ_ROOT/FACADES/SOUTH_HIGH_STREET",
            "CSQ_ROOT/FACADES/EAST_OTHER_PROCEDURAL",
            "CSQ_ROOT/ENTRANCES/WEST_PUBLIC_PLACEHOLDER",
            "CSQ_ROOT/MATERIAL_GROUPS/OPAQUE_CLADDING",
            "CSQ_ROOT/MATERIAL_GROUPS/GLASS",
            "CSQ_ROOT/STRUCTURAL_ELEMENTS",
            "CSQ_ROOT/SIGNAGE_PLACEHOLDERS",
            "CSQ_ROOT/ROOF/MAJOR_PLANE",
        ],
        "visual_qa_cameras": [
            {"camera_id": "qa:csq:north-30th", "position": "approximate street-level northeast of centroid", "target": "north facade center", "fov_deg": 55, "corresponding_reference": "ref:commons:133250280", "confidence": 0.72, "match_status": "PARTIAL"},
            {"camera_id": "qa:csq:south-high-street", "position": "approximate southeast BHS Central pedestrian corridor", "target": "south facade center", "fov_deg": 55, "corresponding_reference": "ref:commons:158404929", "confidence": 0.65, "match_status": "PARTIAL"},
            {"camera_id": "qa:csq:west-5th-high", "position": "high southwest view; exact coordinates unknown", "target": "west facade and roof", "fov_deg": 50, "corresponding_reference": "ref:commons:173664145", "confidence": 0.6, "match_status": "PARTIAL"},
            {"camera_id": "qa:csq:pse-aerial", "position": camera_pse["local_m"] | {"z": "ESTIMATE_FROM_SOURCE_ALTITUDE_OR_VISUAL_MATCH"}, "target": {"x": round(centroid[0], 3), "y": round(centroid[1], 3), "z": 12.95}, "fov_deg": 60, "corresponding_reference": "ref:commons:173664147", "confidence": 0.82, "match_status": "CAMERA_MATCH_READY"},
            {"camera_id": "qa:csq:east-diagnostic", "position": "east-side facade-normal diagnostic", "target": "east facade center", "fov_deg": 50, "corresponding_reference": None, "confidence": 0.2, "match_status": "NOT_POSSIBLE_REFERENCE_MISSING"},
        ],
        "web_performance_constraints": {
            "principle": "LOD and metrics first; no photorealism target",
            "track": ["triangles", "vertices", "materials", "draw_calls", "texture_memory", "GLB_transfer_size", "parse_decode_time"],
            "instructions": ["use shared coarse materials", "instance repeated facade modules where practical", "avoid photo textures for the first pass", "keep signage as optional low-cost placeholders", "generate LOD2/LOD3 from parameters rather than blind decimation"],
        },
        "compute_estimate": {"class": "MODERATE", "reason": "Broad simple massing and a small material set; moderate manual reasoning for three partially evidenced facades and entrance placement."},
        "model_recommendation": {"next_model": "SOL", "astra_required": False, "reason": "Structured dimensions, massing, reference priorities, and approximation rules are sufficient for a deterministic first reconstruction."},
        "readiness": "RECONSTRUCTION_READY_WITH_GAPS",
    }

    write_json(PACKAGE / "massing.json", massing)
    write_json(PACKAGE / "facades.json", facades)
    write_json(PACKAGE / "materials.json", materials)
    write_json(PACKAGE / "entrances.json", entrances)
    write_json(PACKAGE / "observations.json", {"schema_version": 2, "observations": observations, "conflicts": ["obs:csq:above-ground-storeys"]})
    write_json(PACKAGE / "references.json", {"schema_version": 2, "generated_at": NOW, "records": references})
    write_json(PACKAGE / "coverage.json", coverage)
    write_json(PACKAGE / "rights.json", rights)
    write_json(PACKAGE / "unknowns.json", unknowns)
    write_json(PACKAGE / "evidence_gaps.json", gaps)
    write_json(PACKAGE / "reconstruction_spec.json", reconstruction_spec)
    write_json(PACKAGE / "timeline.json", timeline)

    entity["official_address"] = "5th Avenue, Bonifacio High Street Central, Bonifacio Global City, Taguig"
    entity["source_ids"] = sorted(
        set(entity.get("source_ids", []))
        | {
            "source:consultant-campbell-central-square",
            "source:official-ssi-annual-report-2015",
            "source:wikimedia-commons",
        }
    )
    entity["reconstruction_package_version"] = 2
    entity["target_time_state"] = "CURRENT_APPROX_2025_2026"
    entity["reconstruction_readiness"] = "RECONSTRUCTION_READY_WITH_GAPS"
    entity["height"]["evidence_note"] = "Explicit OSM geographic tag audited at way version 5 (2026-04-09); not an authoritative measured survey."
    write_json(PACKAGE / "entity.json", entity)

    readme = f"""# Central Square reconstruction package v2

This is the M6 handoff for `bgc_building_0014` (Central Square, Bonifacio High Street Central). It is self-contained when read with the repository `AGENTS.md` and modeling guidelines. Detailed Blender reconstruction has not started.

## Readiness

**RECONSTRUCTION_READY_WITH_GAPS** for a recognizable LOD1 / medium-fidelity first pass representing approximately 2025–2026 permanent architecture.

Use the existing OSM-derived local-metre geometry as horizontal control. The mapped footprint is {footprint['area_m2']:.2f} m² with an oriented envelope of approximately {footprint['oriented_bounding_box_m']['major']:.2f} × {footprint['oriented_bounding_box_m']['minor']:.2f} m and a mapped maximum height of 25.9 m. The height is explicit OSM geographic evidence, not an authoritative survey.

Target-local sides are:

- north: 30th Street;
- west: 5th Avenue;
- south: Bonifacio High Street / BHS Central pedestrian corridor;
- east: adjacent-building/service side.

The north facade and overall massing are well enough evidenced. West and south are partial. The east/service side, exact public-entry portals, basement access, and roof equipment remain unresolved. Follow `unknowns.json` and the `do_not_invent` rules in `reconstruction_spec.json`.

## Evidence and rights

`references.json` separates reusable Commons files from research-only official, article, and video sources. The 2015 Commons image is correctly classified as an **interior atrium** image, not a facade. No image file is bundled; metadata and source-native hashes are retained. Before redistributing any image or derivative, follow `rights.json` and assemble creator/title/source/license/change attribution.

## Modeling order

1. Load `geometry.geojson` in the existing EPSG:32651-derived local frame.
2. Build the component plan in `massing.json` without changing mapped dimensions.
3. Implement the north, west, and south facade structures from `facades.json`.
4. Use only the placeholder entrance guidance in `entrances.json`.
5. Apply the coarse families in `materials.json`; do not copy research-only imagery or campaign artwork.
6. Render the diagnostic views in `reconstruction_spec.json` and compare only against the linked references.
7. Keep the east facade and roof equipment deliberately low-detail until new evidence exists.

Regenerate this package with:

```powershell
.\\.venv\\Scripts\\python.exe scripts\\reconstruction\\build_central_square_package.py
```

Validate it with:

```powershell
.\\.venv\\Scripts\\python.exe scripts\\reconstruction\\validate_package.py data\\reconstruction_packages\\bgc_building_0014
```
"""
    (PACKAGE / "README.md").write_text(readme, encoding="utf-8")

    assert reference_ids == {item["reference_id"] for item in references}
    print(f"BGC_M6_PACKAGE: references={len(references)} observations={len(observations)} readiness={coverage['reconstruction_readiness']}")


if __name__ == "__main__":
    main()
