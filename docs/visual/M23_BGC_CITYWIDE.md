# M23 — Citywide implementation

108 spatial packages supply mapped building massing, façade families, street markings, safe edge furniture, seven tree archetypes and landscape detail. Geometry is merged by material and primitives are instanced across active packages. Runtime source records are stored separately under data/visual_reference/features. The kit gallery is a reusable source library and is not loaded into the city.

## Evidence and limits

Road markings use mapped lane/cycleway/crossing tags. Intersection signal positions are inferred from mapped nodes and relocated to clear road edges. Unmapped bike lanes and traffic arrangements are not fabricated.

## Reproduce

Run `scripts/m23/run.ps1 -Render` from the repository. Source geometry is in `scripts/m23/build.py`; runtime packages are in `web/public/world/detail/m23`; fixed cameras and hashes are in `data/reports/m23`. Generated Blender and GLB outputs can be recreated.

## Validation

See `data/reports/m23-validation.json`, `m23-performance.json`, `m23-reference-coverage.json` and `m23-visual-acceptance.json`. Static PASS does not grant appearance approval.
