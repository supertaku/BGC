# Pilot geographic QA

QA date: **2026-09-10**. Comparison used the immutable OSM source geometry, the current normalized datasets, fixed Blender renders, and the ULI description of the grid-based center and linear High Street/open-space system.

| Category | Result | Evidence / limitation |
| --- | --- | --- |
| CRS direction and scale | PASS | East/north tests, three geodesic distance comparisons, and 494.0 × 419.2 m pilot dimensions pass automatically. |
| Road topology | PASS | Normalized centerlines preserve 88 clipped OSM highway ways; the aerial render shows the expected orthogonal avenue/street grid without a systematic mirror or rotation. |
| Intersections and block dimensions | PASS | Road/path intersections and the long east-west pedestrian axis align with footprint blocks in the aerial and oblique diagnostics. |
| Building placement | PASS | 31 outlines and 8 parts use source geometry transformed by one CRS module; no per-building manual translation exists. |
| Major pedestrian/open space | PASS | 269 pedestrian features and 21 open-space polygons reproduce the central promenade/parks; non-open `landuse=retail` areas are excluded from the green-space layer. |
| Building heights | PARTIAL | 17 heights are direct OSM tags, 4 use a levels heuristic, and 18 are visibly procedural. Four values above 150 m remain source observations pending external verification. |
| Sidewalk/road widths | PARTIAL | Explicit widths are preserved; missing widths are class-based estimates. These are diagnostic surfaces, not surveyed edges. |
| Overlap consistency | PARTIAL | Two outline overlaps are reported in `PILOT_DATA_AUDIT.md` and retained pending entity-resolution research. |
| Orientation/export | PASS | GLB re-import bounds are consistent and the Three.js viewer uses the exporter axis conversion without a corrective rotation. |

Overall geographic QA: **PASS for low-fidelity pilot placement and topology; PARTIAL for height completeness and derived widths.** No geometry was visually hand-shifted to hide a source issue.
