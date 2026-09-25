# M17R reference QA

Status: **PENDING VISUAL QA**. `data/reports/m17-reference-qa.json` is an independent review record. It tracks silhouette, height, major volume, setback, curvature, facade composition, roof, entrance, material, and ground relationship for each original candidate. Each discrepancy has severity and disposition. A missing view is `NOT_EVIDENCED`, not a pass.

Confirmed open issues in the old draft GLBs:

| Candidate | Aspect | Severity | Evidence |
| --- | --- | --- | --- |
| One Bonifacio | Major volume / entity scope | Critical | OSM mall footprint includes 98.9% of The Suites and 99.5% of PSE tower footprints; the retail component boundary is unresolved. |
| The Suites | Curvature | Major | Generic extrusion omits the architect-described gentle curve. |
| PSE Tower | Facade composition | Major | Old all-edge horizontal bands omit the documented inflected frontpiece and vertical ribs. |
| ACPT | Height | Major | Old GLB uses 114.7 m; SOM reconstruction decision is 136 m. |

PSE massing rounds 1 and 2 produced two generated views per round and a local research-only comparison page at `blender/renders/bgc_m17_0003/comparison.html`. Round 2 introduced an estimated 4 m upper slope, but the twin upper shapes and overlapping tower volumes still differ from the source views. Four source/render pairs are recorded in `m17-reference-qa.json` as `FAIL`. The comparison page references remote copyrighted images and is gitignored; it does not bundle them.

No reference/render comparison has passed and no manual reviewer signoff exists. The old QA presets were not source matched; they are now labeled `DIAGNOSTIC_UNMATCHED`. A reviewer must resolve all evidence-covered critical and major discrepancies. Research-only source images remain remote; the committed record contains source links, render paths, and discrepancy metadata.

`scripts/reconstruction/review_m17.py` reads reviewer records and grants `APPROVED` only when evidence, build, GLB, comparison, discrepancy, and independent-signoff gates all pass. A builder or structural validator cannot set visual approval.
