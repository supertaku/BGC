# Reusable reconstruction playbook

1. Run `python scripts/reconstruction/validate_package.py <package>` and resolve all package errors.
2. Read explicit unknowns, conflicts, coverage, and `do_not_invent` constraints before interpreting geometry.
3. Define local-metre footprint, height envelope, major volumes, and stable component IDs.
4. Build macro geometry first. Keep target-specific massing in the target builder.
5. Build the strongest facade first using normalized `u/v/d` regions and evidence-linked parameters.
6. Generate deterministic reference/oblique/aerial/street QA cameras and review discrepancies.
7. Treat weaker facades conservatively: weak evidence means less geometric specificity.
8. Reuse shared web-PBR material families where appearance genuinely matches.
9. Re-run QA; classify mismatch cause separately from severity and disposition.
10. Save the semantic authoring `.blend`, then create a temporary runtime representation with only explicit safe merges.
11. Export GLB with compact custom properties as extras; re-import, measure, and verify Three.js `userData`.
12. Update the manifest/registry, regenerate the pilot, build production web output, and run fixed-scene browser benchmarks.

Use `scripts/reconstruction/build_building.py --package <package> --stage validate|build|render|full`. `--clean` removes only derived outputs for that entity. Stages remain callable so a material edit does not trigger evidence acquisition.

Routine operation is lighter-model ready: package validation, clean build, metrics, regression, and structured summaries require no architectural reinterpretation. Use Sol for new architectural interpretation, new primitives, or difficult evidence/debugging work.

## M9 demonstrated lessons

- Preserve floor-count conflicts independently from visible band geometry. A model may follow observed bands and an audited height without asserting whether marketing, mezzanine, or mapping conventions are correct.
- Describe an open facade band geometrically first. Assign a parking/mechanical use only when a source supports the function.
- Regular office windows belong in normalized repeat grids. Retain semantic authoring components, then batch identical material/role groups explicitly for runtime.
- When a rooftop frame defines the audited maximum height, keep the main roof below that maximum so the silhouette remains visible; record the roof level as estimated if it is not measured.
- Research-only photography can ground observations without entering the distributable asset. Store URLs, rights state, viewpoints, and observations—not copyrighted image files.

## Error taxonomy

`PACKAGE_ERROR`, `EVIDENCE_ERROR`, `GEOMETRY_ERROR`, `BLENDER_ERROR`, `EXPORT_ERROR`, `METADATA_ERROR`, `ASSET_REGISTRY_ERROR`, `WEB_INTEGRATION_ERROR`, and `PERFORMANCE_WARNING` identify the responsible stage.

No hidden manual state is production input. Encode a manual correction in parameters/script, or record it as a reproducible scripted operation with provenance before approval.

## M10 batch execution

1. Run `python scripts/reconstruction/prepare_m10.py` to refresh candidate selection and packages.
2. Validate/build Wave A with `python scripts/reconstruction/build_batch.py --wave A --stage full --continue-on-error`.
3. Run established-building, generic-fixture, metadata, and GLB regressions.
4. Only after the gate passes, run Wave B. Use `--entity-id ... --retry-count N` for isolated retries.
5. Rebuild the registry-driven pilot, validate the GLB, publish the web manifest, and capture fixed-camera renderer statistics.

Batch failures must retain target-level diagnostics. Package validation always precedes Blender. Research-only imagery remains remote metadata and never becomes a distributed texture.
