# M9 generalization report

## Assessment

**GENERALIZES.** W Global Center was reconstructed through schema 1.0, the same package validator, material library, evidence metadata, QA cameras, authoring checks, runtime exporter, manifest generator, asset registry, and registry-driven pilot substitution used by Central Square. The building-specific module interprets architecture; it does not bypass the framework.

## Reuse accounting

| Classification | Count | Examples |
| --- | ---: | --- |
| EXISTING_SHARED_PRIMITIVE | 7 | FacadeFrame, shared materials, metadata, QA cameras, authoring validation, runtime export/merge, registry/pilot integration |
| NEW_SHARED_PRIMITIVE | 2 | WindowGrid, OpenFacadeBand |
| TARGET_SPECIFIC_CONFIGURATION | 4 | visible band heights, bay counts, corner glazing regions, QA camera transforms |
| TARGET_SPECIFIC_CODE | 2 | evidence-specific builder and diagonal-member placement helper |
| MANUAL_EXCEPTION | 0 | none |

The target builder contains six local functions, but only two encode architectural interpretation; the remaining helpers adapt shared services. Three framework files changed (`geometry/patterns.py`, geometry exports, and generic GLB metrics), plus tests. The reconstruction is mostly configuration-driven with a small evidence-specific builder.

## What changed and what did not

Reused unchanged: schema 1.0, cross-file validation, normalized façade coordinates, all five material families, metadata contract, semantic authoring/runtime separation, GLB extras transport, camera service, lifecycle registry, and pilot replacement.

Extended: two Blender-independent pattern descriptions and generic GLB reporting for vertices/runtime nodes/entity ID. Open bands deliberately describe observed geometry without asserting use. The brochure—not appearance alone—supports the parking interpretation.

Central Square assumptions discovered: the previous real fixture did not exercise dense regular windows, stacked open bands, or a frame that defines maximum height above the main roof. Runtime batching needed to cover repeated architectural roles beyond one façade band/column case.

The first integrated W Global export added 31 draw calls. Explicit metadata-preserving batches reduced the standalone asset from 32 to 12 runtime meshes/calls and the combined pilot to 71 calls. Central Square then rebuilt cleanly, its five renders matched the frozen baseline, and the generic fixture passed.

## Third-building question

Yes. A third office, podium, parking, or regular-window building can reuse the new `WindowGrid` and `OpenFacadeBand` descriptions while retaining the same evidence/package/export path. A more curvilinear, terraced, or tower-and-podium building would still require new massing interpretation, which is the largest remaining generalization weakness.

## Model assessment and next milestone

Sol is **SUFFICIENT_WITH_LIMITATIONS**. Cross-view massing, façade rhythm, conflict preservation, open-band geometry, roof-frame recovery, and runtime optimization succeeded. The limiting factor was source coverage of weak façades and portals, not visual reasoning. Astra was not used and is not required next.

Recommended next milestone: **M10 — Pilot reconstruction batch**. Two architecturally different real buildings now pass the same framework, and the next useful uncertainty is repeated throughput/cost rather than another single-asset proof.
