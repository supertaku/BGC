"""Compact Blender custom properties intended for glTF node extras."""

from __future__ import annotations

import json
from typing import Iterable


ALLOWED_EVIDENCE_STATES = {
    "VERIFIED_AUTHORITATIVE", "VERIFIED_GEOGRAPHIC",
    "VERIFIED_GEOGRAPHIC_NOT_SURVEYED", "VERIFIED_PHOTOGRAPHIC",
    "VERIFIED_STRUCTURED", "INFERRED", "ESTIMATED", "PROCEDURAL",
    "UNKNOWN", "CONFLICTED",
}


def compact_ids(values: Iterable[str]) -> str:
    return json.dumps(list(values), separators=(",", ":"))


def apply_component_metadata(
    obj,
    *,
    entity_id: str,
    component_id: str,
    component_type: str,
    evidence_status: str,
    observation_ids: Iterable[str],
    reconstruction_fidelity: str,
    evidence_ids: Iterable[str] = (),
    target_time_state: str | None = None,
    exportable: bool = True,
):
    if evidence_status not in ALLOWED_EVIDENCE_STATES:
        raise ValueError(f"unsupported evidence status: {evidence_status}")
    observations = list(observation_ids)
    if evidence_status.startswith("VERIFIED") and not observations:
        raise ValueError(f"verified component {component_id} requires observation_ids")
    obj["entity_id"] = entity_id
    obj["component_id"] = component_id
    obj["component_type"] = component_type
    obj["evidence_status"] = evidence_status
    obj["observation_ids"] = compact_ids(observations)
    obj["evidence_ids"] = compact_ids(evidence_ids)
    obj["reconstruction_fidelity"] = reconstruction_fidelity
    if target_time_state:
        obj["target_time_state"] = target_time_state
    obj["exportable"] = exportable
    return obj

