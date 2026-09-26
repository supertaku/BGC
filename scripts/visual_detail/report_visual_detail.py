"""Refresh the M20-M23 evidence and implementation reports from source inputs."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[2]
TODAY = date.today().isoformat()
OUT = ROOT / "data/reports"
DOCS = ROOT / "docs"
SOURCES = {
    "osm": "data/processed/bgc-paths.geojson; data/processed/bgc-open-spaces.geojson; pinned OSM snapshot c7c77bdee83947293624a3a6036089e809c2fb2c1cec4d5283fb1c89535a8ac3",
    "high_street": "https://www.ayalamalls.com/explore/ayala-bonifacio-high-street/store/AYALA-BONIFACIO-HIGH-STREET-1222824",
    "bgc_parks": "https://bgc.com.ph/faqs/",
    "track": "https://bgc.com.ph/directory/track-30th/",
    "central": "https://www.crearis.com.ph/bonifacio-high-street-central/",
    "acpt": "https://arthaland.com/properties/arthaland-century-pacific-tower",
    "uniqlo": "https://www.uniqlo.com/ph/en/special-feature/uniqlo-bgc-high-street",
    "verve": "https://www.alveoland.com.ph/properties/condos/taguig/hss-verve-residences/",
}


def write(name: str, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def doc(name: str, value: str):
    (DOCS / name).write_text(value.strip() + "\n", encoding="utf-8")


def entry(entity, category, source, source_type, geometry, visual, notes, approved, inference, rights="FACTS_ONLY"):
    return {
        "entity_id": entity, "feature_category": category, "source_url": source,
        "source_type": source_type, "rights_status": rights,
        "geometry_confidence": geometry, "visual_confidence": visual,
        "notes": notes, "approved_for_modeling": approved,
        "inference_allowed": inference, "last_reviewed_at": TODAY,
    }


def main():
    package = json.loads((ROOT / "web/public/world/detail/high-street-public-realm.json").read_text(encoding="utf-8"))
    paths = json.loads((ROOT / "data/processed/bgc-paths.geojson").read_text(encoding="utf-8"))["features"]
    parks = json.loads((ROOT / "data/processed/bgc-open-spaces.geojson").read_text(encoding="utf-8"))["features"]
    ids = {source["id"] for tile in package["tiles"].values() for source in tile["sources"]}
    registry = []
    for feature in paths + parks:
        props = feature["properties"]
        if props["id"] not in ids:
            continue
        kind = "park" if props["id"] in ("osm:way:174398019", "osm:way:145147836") else "pedestrian_surface"
        registry.append(entry(props["id"], kind, SOURCES["osm"], "EXISTING_OSM_SNAPSHOT", .8, .35,
                              f"Mapped {props.get('name') or 'crossing'} polygon; appearance and furniture spacing are inferred.", True, True, "ODBL_ATTRIBUTION_REQUIRED"))
    registry.extend([
        entry("high_street_corridor", "pedestrian_boulevard", SOURCES["high_street"], "OFFICIAL_OPERATOR", .35, .75, "Official 1 km boulevard description supports hierarchy, not exact curb or paving pattern.", True, True),
        entry("track_30th", "landscaped_park", SOURCES["track"], "OFFICIAL_DISTRICT", .8, .75, "Official jogging paths, lawns, gardens and art; exact layout comes only from OSM polygons.", True, True),
        entry("terra_28th", "landscaped_park", SOURCES["bgc_parks"], "OFFICIAL_DISTRICT", .8, .6, "Named shaded landscaped park; tree positions are inferred.", True, True),
        entry("high_street_central", "amphitheater_water_plaza", SOURCES["central"], "PROJECT_DESIGNER", .25, .7, "Feature types confirmed but no reusable footprint/grade survey; exact geometry deferred.", False, False),
        entry("bgc_m17_0004", "facade_roof_garden", SOURCES["acpt"], "OFFICIAL_PROPERTY", .7, .65, "ACPT landscaped deck/crown terraces documented; current approved LOD1 retained. Garden outline deferred.", False, False),
        entry("uniqlo_bgc_high_street", "logo_and_art", SOURCES["uniqlo"], "OFFICIAL_BRAND", .15, .7, "Store and mural/Cats of BGC tie confirmed; facade position and reuse rights unresolved.", False, False, "RESEARCH_ONLY"),
        entry("bgc_building_0014", "facade_identity", "data/assets/buildings.json", "APPROVED_PROJECT_ASSET", .85, .8, "Existing Central Square LOD1 contains approved facade detail; no new M23 change.", True, False),
        entry("verve_residences", "open_space_context", SOURCES["verve"], "OFFICIAL_DEVELOPER", .4, .55, "Open-space context supported; exact planter and facade details deferred.", False, True),
    ])
    inventory = [
        ("pavements_sidewalks", "grounded", 5, 5, 2, 2), ("curb_ramps", "deferred", 4, 1, 3, 2),
        ("stairs", "deferred", 3, 1, 3, 2), ("slopes_grade", "deferred", 3, 1, 4, 2),
        ("road_surfaces", "grounded_existing", 5, 5, 1, 1), ("road_markings", "grounded_limited", 4, 3, 2, 2),
        ("medians", "deferred", 3, 1, 2, 2), ("bollards_roadblocks", "grounded_existing", 3, 3, 1, 1),
        ("benches", "inferred", 4, 2, 1, 1), ("bins", "grounded_existing", 2, 3, 1, 1),
        ("bike_racks", "deferred", 2, 2, 2, 1), ("planters", "inferred", 5, 2, 2, 1),
        ("grass_lawns", "grounded_existing", 5, 4, 1, 1), ("trees", "inferred_new_and_grounded_existing", 5, 3, 2, 1),
        ("street_lights", "inferred_new_and_grounded_existing", 4, 2, 1, 1), ("shelters", "deferred", 2, 1, 3, 2),
        ("public_art", "deferred", 3, 2, 4, 2), ("facade_motifs", "grounded_existing", 5, 4, 4, 3),
        ("company_store_logos", "deferred", 3, 2, 3, 2), ("special_identity_markers", "deferred", 3, 2, 3, 2),
    ]
    scope = {
        "schema_version": 1, "milestone": "M20", "status": "PARTIAL", "last_reviewed_at": TODAY,
        "priority_zone": {"primary_local_m_bounds": [-540, -220, 230, 220], "coordinate_frame": "EPSG:32651 minus project origin; x east, y north", "included": ["Bonifacio High Street spine", "High Street Central", "Central Square", "One Bonifacio surroundings", "Track 30th", "Terra 28th"], "secondary": ["High Street South", "De Jesus Oval and Greenway edges"], "note": "Bounding box is an implementation scope, not a legal or architectural boundary."},
        "evidence_registry": registry,
        "feature_inventory": [{"feature_category": a, "status": b, "user_impact_1_to_5": c, "evidence_quality_1_to_5": d, "implementation_cost_1_to_5": e, "runtime_cost_1_to_5": f} for a, b, c, d, e, f in inventory],
        "grounded": ["OSM pedestrian and park polygons", "official High Street boulevard and park identities", "existing approved LOD1 registry"],
        "inferred": ["paving border width", "park-edge strip width", "tree/furniture placement and generic appearance"],
        "deferred": ["surveyed grades, stairs and ramps", "water/amphitheater footprints", "tenant logo positions", "public art geometry"],
        "rejected": ["unverified exact storefronts", "unlicensed mural reproduction"],
    }
    write("m20-visual-evidence-scope.json", scope)

    by_type = {key: sum(len(t["surfaces"].get(key, [])) for t in package["tiles"].values()) for key in ("PAVING_BORDER", "PARK_EDGE", "ZEBRA_CROSSING")}
    by_instance = {key: sum(len(t["instances"].get(key, [])) for t in package["tiles"].values()) for key in ("TREE_CLUSTER", "PLANTER_RECT", "BENCH_LINEAR", "LIGHT_POLE_STANDARD")}
    write("m21-public-realm.json", {"schema_version": 1, "milestone": "M21", "status": "PARTIAL", "source_package": "web/public/world/detail/high-street-public-realm.json", "tile_count": package["counts"]["tiles"], "surface_counts": by_type, "grounded": ["mapped pedestrian polygons", "two OSM zebra crossing polygons"], "inferred": ["0.55 m paving border", "0.65 m park edge"], "deferred": ["curb ramps", "stairs", "slopes", "medians", "plaza and amphitheater feature geometry", "water feature"], "rejected": ["fabricated grade changes"], "validation": "Production build passed; full visual comparison pending."})
    write("m22-streetscape.json", {"schema_version": 1, "milestone": "M22", "status": "PARTIAL", "instance_counts": by_instance, "tile_count": package["counts"]["tiles"], "rendering": "one instanced batch per type across visible detail tiles", "grounded": ["park polygon ownership", "existing mapped environment retained"], "inferred": ["all new furniture positions", "all new tree positions", "generic forms"], "deferred": ["surveyed furniture", "bike racks", "shelters", "night-light behavior"], "rejected": ["distinctive unverified bollard designs"], "validation": "Production build and one foreground High Street inspect frame passed; matched performance study pending."})
    assets = json.loads((ROOT / "data/assets/buildings.json").read_text(encoding="utf-8"))["buildings"]
    approved = [{"entity_id": key, "name": val["name"]} for key, val in assets.items() if val.get("lifecycle", {}).get("lod1") == "APPROVED"]
    write("m23-landmark-facades.json", {"schema_version": 1, "milestone": "M23", "status": "DEFERRED_NEW_WORK", "existing_approved_lod1": approved, "new_facade_assets": 0, "new_logo_assets": 0, "new_art_assets": 0, "grounded": ["existing approved landmark LOD1 assets retained", "official ACPT landscape description", "official UNIQLO BGC art references"], "inferred": [], "deferred": ["new Central Square/ACPT/UNIQLO facade packages", "logos with verified placement and rights", "art marker geometry"], "rejected": ["tenant logo placement without visibility evidence", "copying murals without rights"]})
    write("visual-detail-acceptance.json", {"schema_version": 1, "milestone": "M20-M23", "status": "NOT_YET_ACCEPTED", "release_policy": "PREVIEW_ONLY_detail=1; normal LOW unchanged", "benchmark_observations": "data/reports/visual-detail-benchmark-observations.json", "checks": {"deterministic_tile_ownership": "PASS", "production_build": "PASS", "lint": "PASS", "product_state_and_simulated_tile_lod": "PASS", "street_controls": "PASS", "existing_instancing_fixture": "PASS", "high_street_visual_smoke": "PASS_LIMITED", "complete_search_tour_walk_ui_regression": "UNVERIFIED", "matched_inspect_fps": "PASS_LIMITED_SINGLE_PAIR", "matched_walk_fps": "INCONCLUSIVE_BASELINE_DRIFT", "new_landmark_facade_identity": "NOT_DONE", "logo_art_rights": "DEFERRED"}, "grounded": scope["grounded"], "inferred": scope["inferred"], "deferred": scope["deferred"], "rejected": scope["rejected"]})

    doc("M20_VISUAL_EVIDENCE_SCOPE.md", f"""# M20 visual evidence and scope

**Status: partial.** The machine-readable ledger is [m20-visual-evidence-scope.json](../data/reports/m20-visual-evidence-scope.json). The primary implementation box is x −540…230 m, northing −220…220 m in the project frame. This is a working extent, not an official boundary. Secondary High Street South and western park edges are scoped but not detailed yet.

Grounded: pinned OSM path and park polygons; the [Ayala High Street page]({SOURCES['high_street']}) identifies the 1 km boulevard. The [BGC parks FAQ]({SOURCES['bgc_parks']}) and [Track 30th page]({SOURCES['track']}) support landscaped park character. [Crearis]({SOURCES['central']}) confirms High Street Central's amphitheater, water feature, plaza and gardens but supplies no reusable surveyed geometry.

Inferred: paving and park-edge widths, generic trees, planters, benches and poles. Every generated instance and surface carries its source feature ID and grounding status.

Deferred: grade transitions, exact plaza furnishings, art, and logos. Rejected: unverified storefront precision and unlicensed mural copying. The inventory ranks all requested categories by impact, evidence, implementation cost and runtime cost (1 low, 5 high).
""")
    doc("M21_PUBLIC_REALM_REPORT.md", f"""# M21 public realm

**Status: partial.** The deterministic generator `scripts/visual_detail/build_visual_detail.py` emits {package['counts']['surfaces']} tile-clipped surfaces across {package['counts']['tiles']} tiles: {by_type}. The viewer merges each tile/material surface batch. Existing road and open-space surfaces remain in the base GLBs.

Grounded: mapped High Street pedestrian geometry and zebra-tagged crossings. Inferred: narrow visual border widths. Deferred: surveyed curbs, ramps, stairs, grades, amphitheater and water footprints. Rejected: fabricated height changes. Build passes; matched performance and detailed visual review remain open.
""")
    doc("M22_STREETSCAPE_REPORT.md", f"""# M22 streetscape

**Status: partial.** {package['counts']['instances']} new tile-owned instances: {by_instance}. One instanced draw per visible asset type uses generic low-poly geometry. Existing mapped environment remains intact.

Grounded: park and pedestrian boundaries. Inferred: all added tree and furniture positions and forms. Deferred: verified bike racks, shelters, night lighting, and surveyed placement. Rejected: distinctive unverified designs. New instance placements have no claim of photographic accuracy.
""")
    doc("M23_LANDMARK_FACADE_REPORT.md", f"""# M23 landmark facade and identity

**Status: new work deferred.** {len(approved)} approved LOD1 assets remain in the registry, including Central Square and selected High Street South landmarks. This pass adds no new facade, logo, or art asset.

Grounded research: [ACPT]({SOURCES['acpt']}) documents landscaped deck/crown terraces and plants; [UNIQLO]({SOURCES['uniqlo']}) documents BGC mural and Cats of BGC references; [Alveo Verve]({SOURCES['verve']}) supports open-space context. These sources do not establish precise sign positions or permission to copy artworks. Inferred: none added. Deferred: target-specific facade refinement, rights-reviewed logos, art markers. Rejected: guessed signage and copied murals.
""")
    doc("VISUAL_DETAIL_ACCEPTANCE_REPORT.md", """# Visual detail acceptance

**Gate: not yet accepted. Preview only.** M20 evidence and an M21/M22 first detail layer are implemented. M23 new facade identity and art/signage are still open. The normal LOW default is preserved; enable the experimental layer with `?detail=1`. Use `detail=0`, `detail=surfaces`, or `detail=instances` for diagnostics. No new geometry is allocated when the preview is off.

Production build, lint, deterministic ownership/provenance checks, product-state/search/263 place-link checks, seven simulated LOD handoffs, street-control checks and the existing instancing fixture pass. The foreground High Street scene loads with the new layer and existing LOD1 assets. Full UI search/tour/manual walking regression remains open.

One matched LOW inspect pair measured: detail off 166.20 mean / 163.93 median / 144.93 p1 FPS, 60 calls and 56,988 triangles; detail on 166.30 mean / 163.93 median / 135.14 p1 FPS, 70 calls and 60,398 triangles. Both showed 24 visible tiles, 2 LOD1 assets and zero textures. The optimized layer adds 10 calls and 3,410 triangles at that camera. Its JSON package is about 29 KB and adds no texture assets.

Walking is inconclusive and prevents promotion. The first baseline had p1 140.85 FPS; detailed runs had 93.46 and 67.57 FPS. A later no-detail baseline also fell to 69.44 FPS. This drift prevents attribution to the new layer. Preserve every observation in [visual-detail-benchmark-observations.json](../data/reports/visual-detail-benchmark-observations.json), including failed runs. The scripted walk continues after measurement; renderer counts read later are not synchronized benchmark-end values.

Grounded: source polygons and existing approved assets. Inferred: visual border widths and sparse generic furniture. Deferred: stable walking measurements, complete visual and navigation regression, new landmark facade packages, requested generalized stair/ramp/median builders, rights-reviewed logos and art. Rejected: speculative grade changes and unevidenced logo/art placement. No acceptance claim is made until the open gates pass.

Reproduce data: `.\\.venv\\Scripts\\python.exe scripts/visual_detail/build_visual_detail.py`, then `scripts/visual_detail/verify_visual_detail.py` and `scripts/visual_detail/report_visual_detail.py` with the same interpreter. Preview the production build at `/?view=bgc-high-street&mode=inspect&detail=1`. For benchmark URLs add `debug=1&benchmark=1&quality=LOW`; for scripted walking use `mode=walk&benchmark_walk=1`.
""")
    from report_refinement import main as refinement_report
    refinement_report()
    print("Wrote M20-M23 ledgers and refinement reports")


if __name__ == "__main__":
    main()
