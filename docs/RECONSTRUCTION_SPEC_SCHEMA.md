# Reconstruction specification contract

## Version 1.0

`reconstruction_spec.json` is the human-edited contract for an LOD1 build. The machine-readable contract is `data/schemas/reconstruction-spec-1.0.schema.json`; `scripts/reconstruction/spec_contract.py` supplies dependency-free early validation and stable field-path errors. Versions are semantic strings. Builders reject anything except `"1.0"`; future incompatible changes require an explicit migration rather than silent coercion.

The contract describes decisions, not the complete evidence database. Canonical observations, references, rights, conflicts, and unknowns stay in adjacent package files under `data/reconstruction_packages/<entity_id>/`.

## Required fields

| Section | Purpose |
| --- | --- |
| `target` | Project entity ID, display name, location, and confirmed identity state. |
| `target_time_state` | Architectural time slice and treatment of mutable signage. |
| `geometry_file` | Projected local-metre GeoJSON footprint source. |
| `known_dimensions` | Footprint area/perimeter/bounds, maximum height, and evidence state. |
| `major_building_parts` | Stable semantic component IDs, not Blender object names. |
| `massing_file`, `facades_file`, `entrances_file`, `materials_file` | Cross-file package boundaries validated before Blender starts. |
| `best_reference_ids` and `confidence` | Compact evidence links and decision confidence. |
| `required_procedural_approximations` | Explicit procedural, placeholder, custom, or omitted treatments. |
| `do_not_invent` | Target-specific epistemic constraints. |
| `visual_qa_cameras` | Required repeatable diagnostic views. |
| `web_performance_constraints` | Costs to measure and project-level optimization instructions. |
| `target_fidelity` and `readiness` | LOD meaning and lifecycle gate. |

`generic_builder` is an optional controlled subset for simple/dry-run buildings. It supports box massing volumes, shared material families, numeric QA cameras, and facade regions in normalized coordinates: `u` runs horizontally from 0 to 1, `v` vertically from 0 to 1, and `d_m` is signed facade-normal depth. Distinctive buildings may retain target-specific build logic while using the shared materials, metadata, QA, export, and validation services.

## Evidence/parameter separation

Evidence records report observations and ranges; builder parameters select a reproducible value. Every important generated component links the chosen value to compact `observation_ids`. The observation remains canonical outside Blender.

## Failure behavior

`validate_package.py` checks types/required fields, schema version, referenced files, entity identity, duplicate IDs, material/entrance/observation references, normalized facade segments, rights, evidence states, source IDs, and readiness. Errors use precise paths, for example `reconstruction package invalid: target.entity_id: field required`. Blender is not launched after a package error.

