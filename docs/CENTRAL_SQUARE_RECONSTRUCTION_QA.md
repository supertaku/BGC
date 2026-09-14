# Central Square reconstruction QA

## Result

M7 Central Square LOD1 passes the medium-fidelity acceptance target with documented evidence gaps. The independent asset preserves the OSM-derived local-metre anchor and 25.9 m maximum height, uses 25 export meshes / 356 triangles / 6 materials, and re-imports at the expected location and scale.

## Grounding audit

| Component | State | Basis |
| --- | --- | --- |
| Main footprint and placement | VERIFIED_GEOGRAPHIC | `osm:way:470203066`, EPSG:32651 local frame |
| Maximum height | VERIFIED_GEOGRAPHIC_NOT_SURVEYED | explicit OSM 25.9 m tag |
| Broad low-rise massing and flat roof | VERIFIED_PHOTOGRAPHIC | package massing/roof observations |
| 30th Street large glass/solid regions | VERIFIED_PHOTOGRAPHIC | `ref:commons:133250280` |
| 30th Street broad horizontal bands | ESTIMATED | visible floor organization; exact storey mapping remains conflicted |
| 5th Avenue tall glazed bay | INFERRED | partial west-side photographic coverage |
| West public entrance and canopy | INFERRED / ESTIMATED | public approach supported; exact portal unknown |
| High Street ground recess and tall strip | VERIFIED_PHOTOGRAPHIC | 2025 south-side references |
| High Street coarse columns | PROCEDURAL | supported colonnade relationship, unmeasured spacing |
| East/service facade openings | UNKNOWN / OMITTED | no reliable facade-normal evidence |
| Roof mechanical equipment | UNKNOWN / OMITTED | partial roof coverage only |
| Tenant campaigns and branding | UNKNOWN / OMITTED | mutable and unnecessary for LOD1 |

All significant exported objects carry `entity_id`, `component_id`, `evidence_status`, `observation_ids`, `evidence_ids`, `target_time_state`, and `lod` custom properties. No reference photograph is embedded or redistributed.

## Visual QA

Five deterministic cameras are stored in the standalone `.blend`: `QA_30TH_01`, `QA_5TH_01`, `QA_HIGH_STREET_01`, `QA_CORNER_01`, and `QA_AERIAL_01`. Two focused passes were completed. Pass 1 fixed camera cropping, insufficient diagnostic fill, and weak north-facade band organization. Pass 2 found no CRITICAL or MAJOR LOD1 discrepancy that could be resolved without inventing missing evidence.

The camera matches are approximate except for the geographically anchored aerial overview. No photogrammetric calibration is claimed. Machine-readable findings are in `blender/buildings/bgc_building_0014/qa/discrepancies.json`.

## Remaining unknowns

Exact entrance hierarchy, facade-normal portal geometry, exact mullion spacing, physical storey/directory-label mapping, east/service openings, basement access, and roof plant remain unresolved. They are not silently converted into factual geometry.

## Validation evidence

- Reconstruction package: `VALID_WITH_GAPS`, zero errors and zero warnings.
- Standalone GLB re-import: PASS; bounds X -315.047…-214.465 m, Y 83.805…173.591 m, Z 0…25.9 m.
- Standalone metrics: 51,204 bytes, 25 meshes, 356 triangles, 6 materials, 25 approximate draw calls.
- Pilot GLB re-import: PASS.
- Browser: Central Square saved viewpoint loads, asset is visible in geographic context, and console warning/error count is zero.

