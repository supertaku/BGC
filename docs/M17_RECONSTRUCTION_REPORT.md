# M17 — Priority landmark reconstruction

Status: **FAIL at the visual acceptance gate.** Ten draft LOD1 GLBs passed structural validation; zero new assets passed reference-comparison visual QA, so zero were published. The live world retains the original seven approved LOD1 assets and all LOD2 fallbacks.

Wave A contained four targets; wave B contained six. All were generated from schema-1.0 packages through the existing generic Blender builder, four QA cameras, GLB validator, and asset registry. The assets total 891,512 GLB bytes, 14,992 triangles and approximately 32 additional draw calls **if all ten were simultaneously active**. These are static asset sums, not measured browser costs. Per-building costs are in [m17-building-costs.json](../data/reports/m17-building-costs.json). The preparer and batch runner now keep these entries `PENDING_VISUAL_QA`, and the publisher excludes them.

The package geometry uses geographic polygons, but most appearance was generated as uniform normalized facade bands on every edge. That is procedural filler, not verified photographic evidence. The visible result is too generic for the named landmarks. In particular:

- Arthaland Century Pacific Tower has an unresolved height conflict: the architect's project page describes 136 m while the selected OSM envelope is 114.7 m. Its overlapping-glass facade and roof treatment are not reproduced by the dark striped box. This is a confirmed major discrepancy, not a cosmetic issue.
- The Suites' full-height render is legible after QA-camera repair, but the single generic band rhythm does not reconstruct its documented podium/tower facade composition. This is a confirmed major discrepancy.
- The Mind Museum and Maybank theater are unresolved high-risk silhouettes. Their current QA renders and generic polygon extrusion do not establish the distinct building form. They require new source-matched reviews before any major-discrepancy count can be considered complete.

There are **at least two** confirmed major discrepancies, zero confirmed critical discrepancies, and no complete ten-building discrepancy audit. The original first-round renders were underlit and cropped towers; QA-only ambient/sun lighting and height-aware cameras corrected inspectability for two targets, not the architecture. This is 12 render rounds across ten assets, but **zero passing reference-comparison refinement rounds**. No Astra work was justified: the blockers are unresolved evidence and ordinary modeling work, not a narrow spatial-interpretation failure after multiple focused refinements.

No new shared geometry primitives or target-specific builder modules were added. These generic configurations are a useful cost and pipeline prototype, not completed landmark reconstructions. No LOD0 is warranted yet. The unpublished assets have not had foreground LOD2→LOD1→LOD2 transition or old-asset visual regression validation, so neither check is claimed as passed. Production build and automated tests are separate technical gates; they cannot override this visual failure.

Next work: resolve the ACPT height, compare a fixed camera to each source view, correct massing before facade details, and sign off each asset individually. Use the existing packages and builder; do not republish a draft or advance the M18 gate to PASS merely because a GLB validates.
