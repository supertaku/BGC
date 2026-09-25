"""Dependency-free validation for the formal reconstruction JSON Schema contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"
FIDELITIES = {"LOD0_HIGH_DETAIL_FUTURE", "LOD1_MEDIUM_ARCHITECTURAL_FIDELITY", "LOD2_COARSE_MASSING", "LOD3_DISTANT_PROXY"}
EVIDENCE_STATES = {
    "VERIFIED_AUTHORITATIVE", "VERIFIED_GEOGRAPHIC", "VERIFIED_GEOGRAPHIC_NOT_SURVEYED",
    "VERIFIED_PHOTOGRAPHIC", "VERIFIED_STRUCTURED", "INFERRED", "ESTIMATED",
    "PROCEDURAL", "UNKNOWN", "CONFLICTED",
}


def _object(value: Any, path: str, errors: list[str]) -> dict:
    if not isinstance(value, dict):
        errors.append(f"{path}: expected object")
        return {}
    return value


def _required(record: dict, path: str, fields: tuple[str, ...], errors: list[str]) -> None:
    for field in fields:
        if field not in record:
            errors.append(f"{path + '.' if path else ''}{field}: field required")


def _positive(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
        errors.append(f"{path}: expected positive number")


def validate_spec(payload: Any) -> dict:
    errors: list[str] = []
    spec = _object(payload, "reconstruction_spec", errors)
    _required(spec, "", (
        "schema_version", "target", "target_time_state", "target_fidelity", "geometry_file",
        "known_dimensions", "major_building_parts", "massing_file", "facades_file",
        "entrances_file", "materials_file", "best_reference_ids", "confidence",
        "required_procedural_approximations", "do_not_invent", "visual_qa_cameras",
        "web_performance_constraints", "readiness",
    ), errors)
    if spec.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version: expected {SCHEMA_VERSION!r}")
    target = _object(spec.get("target"), "target", errors)
    _required(target, "target", ("entity_id", "name", "location", "identity_status"), errors)
    if target.get("identity_status") not in {None, "CONFIRMED"}:
        errors.append("target.identity_status: expected 'CONFIRMED'")
    time_state = _object(spec.get("target_time_state"), "target_time_state", errors)
    _required(time_state, "target_time_state", ("value", "permanent_architecture", "tenant_signage_and_seasonal_state"), errors)
    if spec.get("target_fidelity") not in FIDELITIES:
        errors.append(f"target_fidelity: unsupported value {spec.get('target_fidelity')!r}")
    dimensions = _object(spec.get("known_dimensions"), "known_dimensions", errors)
    _required(dimensions, "known_dimensions", ("area_m2", "perimeter_m", "axis_aligned_bounds_m", "maximum_height_m", "height_status"), errors)
    for field in ("area_m2", "perimeter_m", "maximum_height_m"):
        if field in dimensions:
            _positive(dimensions[field], f"known_dimensions.{field}", errors)
    if dimensions.get("height_status") not in EVIDENCE_STATES:
        errors.append("known_dimensions.height_status: unsupported evidence state")
    bounds = _object(dimensions.get("axis_aligned_bounds_m"), "known_dimensions.axis_aligned_bounds_m", errors)
    _required(bounds, "known_dimensions.axis_aligned_bounds_m", ("min_x", "min_y", "max_x", "max_y"), errors)
    if all(isinstance(bounds.get(key), (int, float)) for key in ("min_x", "min_y", "max_x", "max_y")):
        if bounds["max_x"] <= bounds["min_x"] or bounds["max_y"] <= bounds["min_y"]:
            errors.append("known_dimensions.axis_aligned_bounds_m: maxima must exceed minima")
    for field in ("geometry_file", "massing_file", "facades_file", "entrances_file", "materials_file"):
        if field in spec and (not isinstance(spec[field], str) or not spec[field]):
            errors.append(f"{field}: expected non-empty string")
    for field in ("major_building_parts", "do_not_invent", "visual_qa_cameras"):
        if field in spec and (not isinstance(spec[field], list) or not spec[field]):
            errors.append(f"{field}: expected non-empty array")
    if spec.get("readiness") not in {"RECONSTRUCTION_READY", "RECONSTRUCTION_READY_WITH_GAPS"}:
        errors.append("readiness: expected a reconstruction-ready lifecycle state")
    strategy = spec.get("builder_strategy", {"mode": "GENERIC"})
    if not isinstance(strategy, dict) or strategy.get("mode") not in {"GENERIC", "LANDMARK_OVERRIDE"}:
        errors.append("builder_strategy: expected GENERIC or LANDMARK_OVERRIDE")
    elif strategy["mode"] == "LANDMARK_OVERRIDE" and strategy.get("module") != target.get("entity_id"):
        errors.append("builder_strategy.module: must match target entity_id")
    for index, camera in enumerate(spec.get("visual_qa_cameras", [])):
        item = _object(camera, f"visual_qa_cameras[{index}]", errors)
        _required(item, f"visual_qa_cameras[{index}]", ("camera_id", "position", "target", "fov_deg", "corresponding_reference", "confidence", "match_status"), errors)
    if errors:
        raise ValueError("reconstruction package invalid: " + "; ".join(errors))
    return spec


def validate_spec_file(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"reconstruction package invalid: missing {path.name}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"reconstruction package invalid: {path.name}: {exc}") from exc
    return validate_spec(payload)
