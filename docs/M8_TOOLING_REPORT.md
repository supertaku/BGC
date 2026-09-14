# M8 tooling report

## Result

M8 passes. Central Square now rebuilds through shared validation, materials, metadata, QA, export, metrics, and registry services while its evidence-specific massing/facade interpretation remains local to the building. A different synthetic tower fixture passes the generic `u/v/d` facade path, proving the framework does not require Central Square dimensions or volume count.

## Contract and architecture

The reconstruction spec is version `1.0`, documented in `RECONSTRUCTION_SPEC_SCHEMA.md`, and backed by a Draft 2020-12 schema plus dependency-free early/cross-file validation. Eight deliberate failure classes are tested: missing entity ID, invalid material reference, unknown observation ID, malformed facade region, unsupported version, duplicate component ID, missing geometry file, and invalid GLB path.

Shared modules now cover facade coordinates, material families/deduplication, compact evidence-aware component metadata, deterministic QA cameras, authoring validation, runtime export/merging, and draw-call analysis. The one-command staged entry point supports validation, build, render/full work, and clean generated-output removal. `run_m8_fast.ps1` and `run_m8.ps1` separate routine checks from full visual/pilot/web validation.

## Central Square regression and optimization

The semantic authoring fixture remains 25 meshes, 356 triangles, five deterministic cameras, the accepted bounds/25.9 m height, and six runtime materials. All five post-refactor renders had zero mean absolute difference from the frozen M7 images. Binary GLB equality is intentionally not required.

Per-component analysis found two safe batches: four identical-role north facade bands and five nearby south columns. They are merged only in the runtime representation, with source component ID arrays retained in extras. Runtime metrics changed from 25 to 18 meshes/draw calls and from 51,204 to 44,200 bytes; triangles remain 356. The integrated pilot changed from M7's 67 to 60 meshes/draw calls and is 962,916 bytes with 20,076 triangles.

A controlled linked-mesh experiment showed Blender 5.2 emits core glTF shared mesh data for ordinary linked duplicates, not `EXT_mesh_gpu_instancing`; Three.js reuses one geometry across three mesh objects. The extension is supported by both tools but would require a different authoring path. Geometry Nodes and GPU instancing are deferred because the current five-column case is simpler as one local runtime batch.

## Metadata, registry, and QA

Every important component carries entity/component/type/evidence/observation/fidelity metadata. Blender re-import validated all 18 nodes, and the installed Three.js r180 loader exposed extras through `userData`. Full evidence/rights records remain external. A building manifest and lifecycle-aware asset registry now drive pilot replacement, builder loading, and merge policy.

The discrepancy schema distinguishes severity/status from `IMPLEMENTATION_ERROR`, `INTERPRETATION_ERROR`, `INSUFFICIENT_EVIDENCE`, `SOURCE_CONFLICT`, and `INTENTIONAL_LOD_SIMPLIFICATION`. Visual regression produces tolerant metrics and paired images but explicitly does not judge architectural accuracy.

## Benchmark

The first distribution-based production baseline used a 759 × 742 CSS-pixel viewport, fixed DPR 1, 5-second warm-up, and 15-second frame-interval sample on an i5-12500H/15.7 GB system with RTX 3050 Ti and Iris Xe adapters available. The harness did not expose the active adapter or embedded Chromium build, so those fields remain explicitly unavailable rather than guessed.

| Scene | Mean FPS | Median FPS | P1 low | Calls |
| --- | ---: | ---: | ---: | ---: |
| Pilot overview | 165.61 | 163.93 | 149.25 | 60 |
| Central Square near | 165.38 | 163.93 | 149.25 | 40 |
| Central Square street | 165.48 | 166.67 | 149.25 | 31 |

No browser console warning/error was observed. M7 spot values are not treated as a statistical baseline.

## Next target

M9 should reconstruct a second, architecturally unlike real building to test generalization. Current project data identifies W Global Center as confirmed (`bgc_building_0007`), geographically grounded, and morphologically different, but its readiness report still lacks accepted reusable visual references. Treat it as the leading candidate only after that evidence gap is resolved; do not start reconstruction from fame or research-only imagery.

Sol remains the appropriate model for the next architectural interpretation. Luna/Terra can operate routine validation and reporting. Astra is not required.
