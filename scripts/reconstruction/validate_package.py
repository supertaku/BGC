"""Validate a reconstruction package and classify its readiness quality gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from spec_contract import SCHEMA_VERSION, validate_spec


ROOT = Path(__file__).resolve().parents[2]


def read_json(path: Path, errors: list[str]) -> Any:
    if not path.is_file():
        errors.append(f"missing required file: {path.name}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid JSON in {path.name}: {exc}")
        return None


def duplicate_ids(records: list[dict], field: str) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for record in records:
        value = record.get(field)
        if not value:
            continue
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def collect_evidence_ids(value: Any, keys: set[str]) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key in keys and isinstance(child, list):
                found.update(item for item in child if isinstance(item, str))
            else:
                found.update(collect_evidence_ids(child, keys))
    elif isinstance(value, list):
        for child in value:
            found.update(collect_evidence_ids(child, keys))
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    package = args.package.resolve()
    errors: list[str] = []
    warnings: list[str] = []

    required_files = [
        "entity.json",
        "geometry.geojson",
        "massing.json",
        "facades.json",
        "materials.json",
        "entrances.json",
        "observations.json",
        "references.json",
        "coverage.json",
        "rights.json",
        "unknowns.json",
        "evidence_gaps.json",
        "reconstruction_spec.json",
        "timeline.json",
    ]
    payloads = {name: read_json(package / name, errors) for name in required_files}

    if errors:
        result = {"status": "NOT_RECONSTRUCTION_READY", "errors": errors, "warnings": warnings}
        print(json.dumps(result, indent=2) if args.as_json else f"BGC_PACKAGE_VALIDATION: NOT_RECONSTRUCTION_READY errors={len(errors)} warnings=0")
        raise SystemExit(1)

    entity = payloads["entity.json"]
    geometry = payloads["geometry.geojson"]
    references = payloads["references.json"].get("records", [])
    observations = payloads["observations.json"].get("observations", [])
    rights_records = payloads["rights.json"].get("references", [])
    facades = payloads["facades.json"].get("facades", [])
    materials = payloads["materials.json"].get("materials", [])
    entrances = payloads["entrances.json"].get("entrances", [])
    unknowns = payloads["unknowns.json"].get("unknowns", [])
    spec = payloads["reconstruction_spec.json"]
    coverage = payloads["coverage.json"]

    try:
        typed_spec = validate_spec(spec)
    except ValueError as exc:
        errors.append(str(exc))
        typed_spec = None

    if typed_spec and typed_spec["target"]["entity_id"] != entity.get("entity_id"):
        errors.append(
            "reconstruction_spec target.entity_id does not match entity.json entity_id"
        )
    if spec.get("schema_version") != SCHEMA_VERSION:
        errors.append(
            f"unsupported reconstruction schema version {spec.get('schema_version')!r}; "
            f"supported: {SCHEMA_VERSION!r}"
        )
    for file_field in ("geometry_file", "massing_file", "facades_file", "entrances_file", "materials_file"):
        referenced = spec.get(file_field)
        if isinstance(referenced, str) and not (package / referenced).is_file():
            errors.append(f"{file_field} references missing file: {referenced}")

    if entity.get("entity_id") != package.name:
        errors.append(f"entity ID {entity.get('entity_id')!r} does not match package directory {package.name!r}")
    if entity.get("identity_status") != "CONFIRMED":
        errors.append("target identity is not CONFIRMED")
    if not geometry.get("features"):
        errors.append("geometry has no features")
    if geometry.get("projected_crs") != "EPSG:32651":
        errors.append("geometry does not use the project EPSG:32651 frame")

    for records, field, label in [
        (references, "reference_id", "reference"),
        (observations, "observation_id", "observation"),
        (rights_records, "reference_id", "rights"),
        (facades, "facade_id", "facade"),
        (materials, "material_id", "material"),
        (entrances, "entrance_id", "entrance"),
        (unknowns, "unknown_id", "unknown"),
    ]:
        duplicates = duplicate_ids(records, field)
        if duplicates:
            errors.append(f"duplicate {label} IDs: {duplicates}")

    reference_ids = {item.get("reference_id") for item in references}
    rights_ids = {item.get("reference_id") for item in rights_records}
    if reference_ids - rights_ids:
        errors.append(f"references without rights records: {sorted(reference_ids - rights_ids)}")
    if rights_ids - reference_ids:
        errors.append(f"orphan rights records: {sorted(rights_ids - reference_ids)}")

    reusable_rights_required = {
        "creator",
        "license_id",
        "license_url",
        "attribution_text",
        "source_url",
        "share_alike_required",
        "changes_disclosure_required",
    }
    incomplete_reusable_rights = [
        item.get("reference_id")
        for item in rights_records
        if item.get("rights_status") == "REUSE_CAPABLE"
        and any(item.get(field) is None or item.get(field) == "" for field in reusable_rights_required)
    ]
    if incomplete_reusable_rights:
        errors.append(f"reusable references with incomplete rights metadata: {incomplete_reusable_rights}")
    unsafe_research_only = [
        item.get("reference_id")
        for item in rights_records
        if item.get("rights_status") == "RESEARCH_ONLY"
        and any(item.get(field) is not False for field in ("local_copy_allowed", "derivative_use_allowed", "redistribution_allowed"))
    ]
    if unsafe_research_only:
        errors.append(f"research-only references with unsafe use flags: {unsafe_research_only}")

    material_ids = {item.get("material_id") for item in materials}
    observation_ids = {item.get("observation_id") for item in observations}
    entrance_ids = {item.get("entrance_id") for item in entrances}
    unresolved_materials = sorted(
        {item for facade in facades for item in facade.get("material_regions", [])} - material_ids
    )
    unresolved_entrances = sorted(
        {item for facade in facades for item in facade.get("entrances", [])} - entrance_ids
    )
    if unresolved_materials:
        errors.append(f"unresolved facade material IDs: {unresolved_materials}")
    if unresolved_entrances:
        errors.append(f"unresolved facade entrance IDs: {unresolved_entrances}")

    generic = spec.get("generic_builder", {})
    generic_components = list(generic.get("volumes", [])) + list(generic.get("facade_regions", []))
    duplicate_components = duplicate_ids(generic_components, "component_id")
    if duplicate_components:
        errors.append(f"duplicate component IDs: {duplicate_components}")
    unknown_observations = sorted({
        observation_id
        for component in generic_components
        for observation_id in component.get("observation_ids", [])
        if observation_id not in observation_ids
    })
    if unknown_observations:
        errors.append(f"unknown observation IDs: {unknown_observations}")
    for index, region in enumerate(generic.get("facade_regions", [])):
        required = {"u0", "u1", "v0", "v1", "thickness_m", "frame"}
        missing = sorted(required - set(region))
        if missing:
            errors.append(f"generic_builder.facade_regions[{index}] missing: {missing}")
            continue
        if not (0 <= region["u0"] < region["u1"] <= 1 and 0 <= region["v0"] < region["v1"] <= 1):
            errors.append(f"generic_builder.facade_regions[{index}] has malformed normalized segment")

    entrance_side_by_id = {item.get("entrance_id"): item.get("side", "") for item in entrances}
    side_mismatches = []
    for facade in facades:
        facade_side = facade.get("orientation", "").split("_", 1)[0]
        for entrance_id in facade.get("entrances", []):
            entrance_side = entrance_side_by_id.get(entrance_id, "").split("_", 1)[0]
            if facade_side and entrance_side and facade_side != entrance_side:
                side_mismatches.append(f"{facade.get('facade_id')} -> {entrance_id}")
    if side_mismatches:
        errors.append(f"facade/entrance side mismatches: {side_mismatches}")

    sources = read_json(ROOT / "data" / "sources" / "sources.json", errors)
    source_ids = {item.get("source_id") for item in sources.get("sources", [])} if sources else set()
    used_sources = collect_evidence_ids(payloads, {"source_ids"})
    used_sources.update(item.get("source_id") for item in references if item.get("source_id"))
    # Geometry records deliberately retain provider-native feature IDs beside
    # registry IDs (for example ``osm:way:205968610`` and ``source:osm``).
    # Only registry-shaped IDs are expected to resolve in sources.json.
    registry_sources = {item for item in used_sources if item.startswith("source:")}
    missing_sources = sorted(registry_sources - source_ids)
    if missing_sources:
        errors.append(f"unresolved source IDs: {missing_sources}")

    used_references = collect_evidence_ids(
        {
            name: payload
            for name, payload in payloads.items()
            if name not in {"references.json", "rights.json"}
        },
        {"reference_ids", "evidence_ids", "best_reference_ids", "identity_reference_ids", "accepted_visual_reference_ids", "reusable_visual_reference_ids", "research_only_visual_reference_ids"},
    )
    used_references.update(
        item
        for observation in observations
        for item in observation.get("reference_ids", [])
    )
    unresolved_references = sorted(item for item in used_references if item.startswith("ref:") and item not in reference_ids)
    if unresolved_references:
        errors.append(f"unresolved reference IDs: {unresolved_references}")

    referenced_by_package = used_references | {item for item in spec.get("best_reference_ids", []) if item.startswith("ref:")}
    orphan_references = sorted(reference_ids - referenced_by_package)
    if orphan_references:
        warnings.append(f"references retained but not used by downstream package fields: {orphan_references}")

    allowed_statuses = {
        "VERIFIED_AUTHORITATIVE",
        "VERIFIED_GEOGRAPHIC",
        "VERIFIED_PHOTOGRAPHIC",
        "VERIFIED_STRUCTURED",
        "INFERRED",
        "ESTIMATED",
        "PROCEDURAL",
        "UNKNOWN",
        "CONFLICTED",
    }
    unsupported = [item.get("observation_id") for item in observations if item.get("status") not in allowed_statuses]
    if unsupported:
        errors.append(f"observations with unsupported status: {unsupported}")
    ungrounded = [
        item.get("observation_id")
        for item in observations
        if not item.get("source_ids") and item.get("status") not in {"UNKNOWN", "PROCEDURAL"}
    ]
    if ungrounded:
        errors.append(f"observations without source evidence or explicit unknown/procedural status: {ungrounded}")

    if not spec.get("do_not_invent"):
        errors.append("reconstruction_spec has no do-not-invent constraints")
    if not unknowns:
        errors.append("unknowns.json has no explicit unknowns")

    critical_ratings = coverage.get("aspects", {})
    for aspect in spec.get("required_coverage_aspects", ["overall_massing", "materials"]):
        if critical_ratings.get(aspect, {}).get("rating") in {None, "NONE"}:
            errors.append(f"critical aspect lacks usable coverage: {aspect}")

    declared = coverage.get("reconstruction_readiness")
    if errors:
        status = "NOT_RECONSTRUCTION_READY"
    elif declared == "RECONSTRUCTION_READY" and not unknowns:
        status = "VALID"
    elif declared in {"RECONSTRUCTION_READY", "RECONSTRUCTION_READY_WITH_GAPS"}:
        status = "VALID_WITH_GAPS"
    else:
        status = "NOT_RECONSTRUCTION_READY"
        errors.append(f"unsupported or non-ready declared state: {declared!r}")

    result = {
        "status": status,
        "package": str(package),
        "entity_id": entity.get("entity_id"),
        "counts": {
            "geometry_features": len(geometry.get("features", [])),
            "references": len(references),
            "rights_records": len(rights_records),
            "observations": len(observations),
            "facades": len(facades),
            "materials": len(materials),
            "entrances": len(entrances),
            "unknowns": len(unknowns),
        },
        "errors": errors,
        "warnings": warnings,
    }
    if args.as_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"BGC_PACKAGE_VALIDATION: {status} errors={len(errors)} warnings={len(warnings)}")
        for warning in warnings:
            print(f"WARNING: {warning}")
        for error in errors:
            print(f"ERROR: {error}")
    raise SystemExit(1 if status == "NOT_RECONSTRUCTION_READY" else 0)


if __name__ == "__main__":
    main()
