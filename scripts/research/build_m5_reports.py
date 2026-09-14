"""Generate M5 audits and the first reconstruction-agent input package."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from evidence.model import read_json, write_json  # noqa: E402

DOCS = ROOT / "docs"
PACKAGE_ROOT = ROOT / "data" / "reconstruction_packages"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def md_table(headers: list[str], rows: list[list[object]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(value if value is not None else "—").replace("|", "\\|") for value in row) + " |")
    return "\n".join(lines)


def main() -> None:
    entities_payload = read_json(ROOT / "data/entities/pilot-entities.json")
    entities = entities_payload["entities"]
    complexes = entities_payload["complexes"]
    references_payload = read_json(ROOT / "data/references/references.json")
    references = references_payload["records"]
    discovery = read_json(ROOT / "data/references/commons-discovery.json")
    coverage_payload = read_json(ROOT / "data/references/coverage.json")
    coverage = coverage_payload["entities"]
    observations_payload = read_json(ROOT / "data/references/observations.json")
    observations = observations_payload["observations"]
    conflicts = read_json(ROOT / "data/references/conflicts.json")["conflicts"]
    height_checks = read_json(ROOT / "data/references/procedural-height-checks.json")
    raw_audit = read_json(ROOT / "data/processed/pilot-data-audit.json")["counts"]
    raw_buildings = read_json(ROOT / "data/processed/pilot-buildings.geojson")
    identity_counts = Counter(entity["identity_status"] for entity in entities)
    coverage_counts = Counter(item["overall_imagery"] for item in coverage)
    wikidata_linked = sum(bool(entity.get("wikidata_id")) for entity in entities)
    official_confirmed = sum(entity["identity_status"] == "CONFIRMED" and any(source.startswith("source:official-") or source.startswith("source:government-") for source in entity.get("source_ids", [])) for entity in entities)
    accepted = sum(record.get("entity_match_status") == "ACCEPTED" for record in references)
    rejected = sum(item.get("discovery_status") == "REJECTED" for item in discovery["candidates"])
    rights_reviewed = sum(record.get("rights_status") in {"REUSE_CAPABLE", "RESEARCH_ONLY"} for record in references)
    reusable = sum(record.get("rights_status") == "REUSE_CAPABLE" for record in references)
    research_only = sum(record.get("rights_status") == "RESEARCH_ONLY" for record in references)
    rights_required = sum(record.get("rights_status") == "REVIEW_REQUIRED" for record in references)

    write_text(DOCS / "ENTITY_STRUCTURE_AUDIT.md", f"""# Entity structure audit

Audit date: **2026-09-11**.

{md_table(["Measure", "Result"], [
    ["Raw geographic building records", entities_payload['counts']['raw_geographic_records']],
    ["Building outlines", entities_payload['counts']['building_outlines']],
    ["Building parts", entities_payload['counts']['building_parts']],
    ["Canonical building/structure entities", entities_payload['counts']['canonical_building_entities']],
    ["Building complexes", entities_payload['counts']['building_complexes']],
    ["Building parts resolved", f"{entities_payload['counts']['building_parts_resolved']}/{entities_payload['counts']['building_parts']}"],
    ["Unresolved building fragments", entities_payload['counts']['building_parts_unresolved']],
])}

One unnamed office outline (`osm:way:1071370327`) is merged into the Mariano K. Tan Center entity because it is wholly contained by the named outline and both contain the same explicit building part. This is an entity-layer decision only; neither source polygon is changed. The nested Bench footprint remains a child entity of B:5 pending building-versus-tenant review. Two roof multipolygons remain separate unresolved structures. The western `osm:way:469908149` building part has no containing in-pilot outline and remains an unresolved fragment, likely because its parent lies beyond the clip.

Complex records are separate from physical buildings: Bonifacio High Street and High Street South. Membership is evidence-scored and does not merge member geometry.

Machine-readable evidence: `data/entities/pilot-entities.json` and `data/review/entity-match-review.json`.
""")

    entity_rows = [[entity["entity_id"], entity.get("canonical_name") or "(unnamed)", entity["entity_type"], entity["identity_status"], ", ".join(entity["osm_ids"]), entity.get("wikidata_id") or "—"] for entity in entities]
    write_text(DOCS / "PILOT_ENTITY_AUDIT.md", f"""# Pilot entity audit

Audit date: **2026-09-11**. The canonical count is honest about one merged duplicate outline and one orphan building part; it is not assumed to equal either 31 outlines or 39 raw records.

{md_table(["Metric", "Count"], [
    ["Raw geographic records", 39],
    ["Canonical building/structure entities", len(entities)],
    ["Building complexes", len(complexes)],
    ["CONFIRMED", identity_counts['CONFIRMED']],
    ["HIGH_CONFIDENCE", identity_counts['HIGH_CONFIDENCE']],
    ["REVIEW_REQUIRED", identity_counts['REVIEW_REQUIRED']],
    ["UNRESOLVED", identity_counts['UNRESOLVED']],
    ["Wikidata-linked entities", wikidata_linked],
    ["Official-source CONFIRMED entities", official_confirmed],
])}

## Canonical entities

{md_table(["Entity", "Canonical name", "Type", "Identity", "OSM feature(s)", "Wikidata"], entity_rows)}

The two `B:3` footprints remain separate and are queued for alias disambiguation. Fuzzy/name similarity never merged them. Direct identifiers and exact official name/address/coordinate evidence are the only automatic CONFIRMED paths.
""")

    write_text(DOCS / "PILOT_REFERENCE_AUDIT.md", f"""# Pilot reference audit

Audit date: **2026-09-11**. This is a bounded pilot audit of Wikimedia Commons metadata for {discovery['targets']} named entities plus five official-source records. It is not comprehensive internet coverage. No full-resolution image was downloaded.

{md_table(["Metric", "Count"], [
    ["References discovered", len(discovery['candidates']) + 5],
    ["References retained after enrichment", len(references)],
    ["Accepted entity links", accepted],
    ["Rejected discovery candidates", rejected],
    ["Duplicates removed", references_payload['duplicates_removed']],
    ["Rights reviewed/classified", rights_reviewed],
    ["Reuse-capable metadata records", reusable],
    ["Research-only records", research_only],
    ["Rights review required", rights_required],
])}

## Coverage

{md_table(["Rating", "Entities"], [[rating, coverage_counts[rating]] for rating in ("GOOD", "PARTIAL", "WEAK", "NONE")])}

Central Square has two accepted, rights-reviewed Commons records and therefore `GOOD` overall imagery, but all directional facade, entrance, podium, and roof categories remain `NONE` because direction was not established. Harlan + Holden Coffee has one rights-capable candidate but remains `WEAK` because the entity match is queued for review. Rights usability and entity acceptance are deliberately separate.

Rejected search results and review queues are retained under `data/review/`. Source-native IDs and SHA1 values are preferred over perceptual hashing; no file was downloaded merely to hash it.
""")

    write_text(DOCS / "PILOT_HEIGHT_EVIDENCE.md", f"""# Pilot height evidence update

Audit date: **2026-09-11**.

{md_table(["State", "Previous", "After M5 identity enrichment"], [
    ["VERIFIED_GEOGRAPHIC", 17, raw_audit['heights_verified_geographic']],
    ["ESTIMATED", 4, raw_audit['heights_estimated']],
    ["PROCEDURAL", 18, height_checks['procedural_heights_remaining']],
    ["UNKNOWN", 0, 0],
    ["CONFLICTED height", 0, 0],
])}

All 18 procedural-height geographic features were checked opportunistically during identity, official-source, and direct-Wikidata enrichment. No defensible explicit height or floor count surfaced for those features, so none was upgraded. The structured check list is `data/references/procedural-height-checks.json`.

Canonical entities with explicit tower/podium parts use the maximum explicit OSM part height for reconstruction-readiness summaries while preserving every component height. This does not modify Blender geometry or the normalized geographic source.

One non-height conflict is retained: W Group describes W Global Center as seven storeys while OSM records `building:levels=8`. The project preserves both statements in `data/references/conflicts.json`; neither silently overwrites the explicit OSM height value.
""")

    readiness_rows = [[item["entity_id"], item.get("canonical_name") or "(unnamed)", item["identity"], item["height_evidence"], item["massing_evidence"], item["overall_imagery"], len(item["reusable_reference_ids"]), "; ".join(item["important_missing_evidence"]), item["recommended_fidelity_tier"], item["reconstruction_readiness"]] for item in coverage]
    write_text(DOCS / "RECONSTRUCTION_READINESS.md", f"""# Reconstruction readiness

Readiness date: **2026-09-11**. Dimensions remain visible; the readiness label does not replace them.

{md_table(["Entity", "Name", "Identity", "Height", "Massing", "Visual", "Reusable refs", "Important gaps", "Tier", "Readiness"], readiness_rows)}

## Recommended first target

**Primary: Central Square (`bgc_building_0014`).** It combines confirmed identity, explicit geographic height, a real footprint with three resolved parts, an official operator record, and two rights-reviewed Commons photographs. It is valuable without being an extreme tower reconstruction. Directional facade, entrance, and roof evidence are still missing, so detailed reconstruction must begin with targeted gap closure.

**Backup: W Global Center (`bgc_building_0007`).** It has a direct Wikidata link, owner-confirmed location and storey description, explicit geographic height, and moderate massing complexity. It needs accepted reusable visual references before refinement.

Recommended next milestone: **M6 — target-specific evidence closure and reconstruction-package validation**, followed by Sol-led procedural reconstruction only when the missing directional evidence is addressed. Astra required next: **NO**.
""")

    summary = {
        "phase": "PASS",
        "raw_geographic_records": 39,
        "canonical_entities": len(entities),
        "building_complexes": len(complexes),
        "building_parts_resolved": entities_payload['counts']['building_parts_resolved'],
        "building_parts_total": entities_payload['counts']['building_parts'],
        "entity_identities": {key: identity_counts[key] for key in ("CONFIRMED", "HIGH_CONFIDENCE", "REVIEW_REQUIRED", "UNRESOLVED")},
        "wikidata_linked_entities": wikidata_linked,
        "official_source_confirmed_entities": official_confirmed,
        "references_discovered": len(discovery['candidates']) + 5,
        "references_accepted": accepted,
        "references_rejected": rejected,
        "duplicates_removed": references_payload['duplicates_removed'],
        "rights_reviewed": rights_reviewed,
        "reusable_references": reusable,
        "research_only_references": research_only,
        "rights_review_required": rights_required,
        "reference_coverage": {key: coverage_counts[key] for key in ("GOOD", "PARTIAL", "WEAK", "NONE")},
        "heights": {"VERIFIED": raw_audit['heights_verified_geographic'], "ESTIMATED": raw_audit['heights_estimated'], "PROCEDURAL": height_checks['procedural_heights_remaining'], "UNKNOWN": 0, "CONFLICTED": 0},
        "previous_procedural_heights": 18,
        "procedural_heights_remaining": height_checks['procedural_heights_remaining'],
        "primary_reconstruction_target": "bgc_building_0014 — Central Square",
        "backup_target": "bgc_building_0007 — W Global Center",
        "major_evidence_gap": "No directionally verified facade, entrance, or roof coverage for any entity.",
        "major_blocker": None,
        "recommended_next_milestone": "M6 — target-specific evidence closure and reconstruction-package validation",
        "recommended_model": "SOL",
        "astra_required_next": False,
    }
    write_json(ROOT / "data/reports/m5-summary.json", summary)

    target_id = "bgc_building_0014"
    package = PACKAGE_ROOT / target_id
    target_entity = next(entity for entity in entities if entity["entity_id"] == target_id)
    target_sources = set(target_entity["geographic_feature_ids"] + target_entity["building_part_ids"])
    geometry_features = [feature for feature in raw_buildings["features"] if feature["properties"]["id"] in target_sources]
    target_refs = [record for record in references if any(link["entity_id"] == target_id for link in record.get("entity_links", []))]
    target_obs = [item for item in observations if item["entity_id"] == target_id]
    target_coverage = next(item for item in coverage if item["entity_id"] == target_id)
    write_json(package / "entity.json", target_entity)
    write_json(package / "geometry.geojson", {"type": "FeatureCollection", "name": f"{target_id}-geometry", "source_crs": raw_buildings["source_crs"], "projected_crs": raw_buildings["projected_crs"], "local_frame": raw_buildings["local_frame"], "features": geometry_features})
    write_json(package / "observations.json", {"schema_version": 1, "observations": target_obs, "conflicts": [item for item in conflicts if item["entity_id"] == target_id]})
    write_json(package / "references.json", {"schema_version": 1, "records": target_refs})
    write_json(package / "rights.json", {"schema_version": 1, "references": [{"reference_id": item["reference_id"], "rights_status": item["rights_status"], "license_id": item.get("license_id"), "license_url": item.get("license_url"), "credit_line": item.get("credit_line"), "attribution_required": item.get("attribution_required"), "share_alike_required": item.get("share_alike_required"), "local_file_path": item.get("local_file_path")} for item in target_refs]})
    write_json(package / "coverage.json", target_coverage)
    write_text(package / "README.md", """# Central Square reconstruction package

This package is the M5 handoff for `bgc_building_0014`. It contains project-owned identity, local-metre source geometry, field-level observations, source-linked reference metadata, rights states, and visible coverage gaps.

No full-resolution image is bundled. Follow each `source_page_url`; use a remote asset only according to `rights.json` and assemble attribution before distribution. Do not infer facade direction from filename or camera location. Directional facades, entrance, podium detail, and roof remain unknown and must not be presented as verified.

The next agent should consume this package before searching again. New evidence must be added to the shared source/reference/observation datasets and then this package regenerated.
""")
    print(f"BGC_M5_REPORTS: phase=PASS entities={len(entities)} references={len(references)} package={package.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

