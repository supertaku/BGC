# W Global Center reconstruction QA

## Result

LOD1 QA is **PASS WITH EVIDENCE-LIMITED DETAIL**. Five deterministic cameras cover 30th Street, 9th Avenue, the important corner, a weak-side diagnostic, and aerial massing.

The first pass exposed two implementation errors: the main solid incorrectly occupied the frame-inclusive 30.5 m envelope, hiding the rooftop opening, and street cameras were too tight for whole-façade comparison. The solid roof was lowered to an estimated 27.5 m while the observed frame retains the 30.5 m maximum, and the cameras were widened. No CRITICAL or MAJOR implementation discrepancy remains.

| Area | Result | Evidence-aware disposition |
| --- | --- | --- |
| Massing | PASS | Mapped footprint and unchanged maximum height |
| Primary corner | PASS | Glazed corner, open bands, window rhythm, and roof frame retained |
| Secondary street façade | PASS | Same broad language with evidence-supported variation |
| Weak façades | PASS | Intentionally plain; no invented service openings |
| Roof | PASS | Major frame represented; machinery omitted |
| Materials | PASS | Five existing shared material families; no photo textures |

Remaining limitations are `BLOCKED_BY_EVIDENCE`: exact entrance/door geometry, weak-side openings, exact mullion spacing, and exact frame connections. The physical-storey mismatch is `SOURCE_CONFLICT`, not a geometry defect.

QA renders are under `blender/buildings/bgc_building_0007/renders/final/`; the structured discrepancy record is `blender/buildings/bgc_building_0007/qa/discrepancies.json`.
