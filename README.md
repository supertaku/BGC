# BGC 3D Tour

Reproducible geospatial 3D pipeline from OpenStreetMap through normalized local-metre data, Blender, tiled GLB, and a Three.js engineering viewer. The current deliverable is a low-fidelity whole-BGC skeleton; it is diagnostic massing, not detailed architectural reconstruction.

## M11 whole city

Regenerate the cached whole-city pipeline and validate it end to end:

```powershell
./scripts/validation/run_m11.ps1
```

Use `-RefreshOsm` only for an intentional refresh and `-ForceTiles` only when unchanged tile outputs must be rebuilt. The pipeline fetches the estimated working boundary in bounded official OSM API cells, normalizes it in the established CRS, assigns 250 m tiles, performs part-aware extrusion, exports and caches each GLB independently, publishes the viewer manifest, runs M11 tests, and builds the production web app. See `docs/M11_WHOLE_BGC_REPORT.md`.

## Grounded pilot

Create the local geospatial environment once:

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements-geospatial.txt
```

Regenerate from cached external inputs:

```powershell
./scripts/validation/run_pilot_experiment.ps1
./scripts/validation/check_outputs.ps1
```

Use `-RefreshOsm` or `-RefreshReferences` only for an intentional upstream refresh. Normal runs reuse immutable cached responses.

Run the viewer:

```powershell
Set-Location web
npm run dev
```

Open <http://localhost:3000>. The page loads `bgc-pilot-base.glb`, shows OSM attribution and height-evidence colors, exposes saved inspection viewpoints, and reports FPS/calls/triangles.

Generated Blender scenes, renders, copied viewer GLBs, and build outputs are reproducible and ignored by Git. Raw/processed source data, scripts, metadata, manifests, and audit documents are versioned.

## M5 evidence layer

Rebuild canonical entities, cached enrichments, rights decisions, coverage, reports, and the Central Square reconstruction package:

```powershell
./scripts/validation/run_m5.ps1
```

The default run is offline/cache-first. Use `-RefreshReferences` only for an intentional, bounded upstream metadata refresh. M5 downloads no full-resolution photographs. Detailed results live in `docs/PILOT_ENTITY_AUDIT.md`, `docs/PILOT_REFERENCE_AUDIT.md`, `docs/PILOT_HEIGHT_EVIDENCE.md`, and `docs/RECONSTRUCTION_READINESS.md`.
