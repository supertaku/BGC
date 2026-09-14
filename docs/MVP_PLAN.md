# MVP plan

## Repository review

### Reuse

- Keep `scene_tools.py` for deterministic scene setup, materials, simple massing, repeated linked meshes, cameras, renders, saves, and GLB export.
- Keep the PowerShell Blender discovery and validation pattern.
- Keep metre units and exporter-owned Z-up → Y-up conversion.
- Keep the Next.js/R3F viewer, loading state, error boundary, OrbitControls, and stats as the integration shell.
- Keep generated `.blend`, PNG, and GLB files out of version control; commit source data, scripts, metadata, and small raw/processed fixtures.

### Extend

- Geographic normalization needs OSM relation/multipolygon assembly, holes, building parts, topology validation, roads/paths/open spaces, and explicit source diffs.
- The exporter can produce multiple assets in separate clean runs, but it lacks collection/tile selection, per-asset manifests, compression policy, and metrics. Extend it; do not replace it.
- The viewer now loads one GLB through a world manifest. Introduce tile lifecycle and imperative loaders before implementing streaming.
- Add asset metrics (triangles, draw calls/material slots, texture bytes, GLB bytes) to validation outputs.

### Leave untouched for now

- Do not rewrite the bootstrap scene generators or replace Next.js/R3F.
- Do not add a backend, database server, ECS, physics engine, global state library, or advanced renderer.
- Do not add facade detail until entity matching and reference coverage are populated.

## MVP-A — pilot quality

Create a geographically consistent, navigable 20.35-hectare High Street central-core reconstruction with a procedural base, several real footprint-derived buildings, and at least one evidence-refined recognizable Tier A/B building. The pilot validates quality, provenance, regeneration, and nearby web performance.

Recommended navigation is **bounded orbit/fly with saved viewpoints**. Orbit remains useful for reconstruction QA; a constrained fly camera makes the space feel like a tour without requiring character animation, stairs, or production collision. First-person walking can follow after scale and collision proxies are trustworthy. Guided camera stops can reuse the same viewpoints.

### Acceptance criteria

**Geographic**

- All imported horizontal geometry passes through EPSG:32651 and the fixed local origin; no ad-hoc degree arithmetic exists in Blender or the viewer.
- Pilot roads/buildings align without visible systematic offset; at least three surveyed/map-known cross-check distances are within the source's documented or observed tolerance.
- Tile/asset bounds and scene units are metres and validated automatically.

**Reconstruction**

- At least 10 buildings are generated from real footprints; at least one Tier A/B building is recognizable from evidence-backed silhouette/material/entrance cues.
- Every height and facade aspect has an evidence class. Missing sides/roofs are `UNKNOWN` or visibly procedural, not implied to be verified.
- Roads, sidewalks, pedestrian space, vegetation, and representative furniture are present as systems, not one-off sculptures.

**Pipeline**

- A clean checkout with cached inputs regenerates processed data, tile scene, diagnostic renders, and GLB deterministically.
- Raw source hash, retrieval timestamp, license/attribution, transform version, generator version, and entity IDs survive to asset metadata.
- Export and GLB re-import validation are automated.

**Web**

- The pilot loads from a manifest, exposes visible OSM attribution, supports bounded orbit/fly and saved viewpoints, and reports no critical console/runtime errors.
- On named baseline desktop hardware, the representative street and aerial views meet the provisional FPS/draw-call/memory budgets below. Mobile fallback is explicitly tested or disabled with a clear message.

**Engineering**

- A second tile/building can be added from data without editing viewer component code or duplicating a Blender scene manually.
- Generated base assets and manual Tier A/B overrides remain separable.

## MVP-B — whole-BGC scale

Generate and stream a low-fidelity skeleton over the versioned working boundary: footprints, trustworthy/estimated heights, major roads/paths/open spaces and landmarks in correct relative positions. Most buildings remain Tier C procedural masses.

### Acceptance criteria

- The entire working polygon is queried and normalized with an auditable coverage report; gaps are reported rather than hidden.
- Hundreds of buildings are generated if supported by the source extract, with stable IDs and explicit height evidence.
- 250 m tiles build independently; cross-boundary buildings, clipped roads, seams, and shared landmark visibility pass automated checks.
- City navigation crosses tile boundaries while assets load/unload without duplicated entities, obvious gaps, runaway requests, or critical errors.
- At least three LOD levels are demonstrated on representative buildings; selection has hysteresis and measurable triangle reduction.
- A named desktop and constrained/mobile profile maintain stable memory over a 10-minute traversal and meet revised evidence-based budgets.
- Detailed facade accuracy is not an acceptance requirement outside the refined pilot/landmark set.

## Web runtime architecture

Build only the first four modules for MVP-A:

```text
WorldManager (origin, coordinate contract, manifest)
    -> TileManager (working set and lifecycle)
        -> AssetLoader (GLB cache, cancellation, disposal)
        -> LODManager (screen-size policy and hysteresis)
NavigationController (bounded orbit/fly and viewpoints)
PerformanceMonitor (FPS, draw calls, triangles, memory where exposed)
```

`POIManager` and `TourController` consume stable entity/viewpoint IDs after the manifest exists. `CollisionSystem` starts with simplified ground/building proxies only when fly-to-walk work begins. Per-frame camera/LOD work stays in Three.js refs/useFrame or standalone managers; React state is reserved for low-frequency UI state and summaries.

## Provisional pilot budgets

These are hypotheses to test, not promises. Revise them after M10 on named devices.

| Metric | Desktop pilot target | Constrained/mobile fallback | Measurement |
| --- | ---: | ---: | --- |
| Visible triangles | ≤ 350k typical, ≤ 600k worst saved view | ≤ 150k typical | `renderer.info.render.triangles` sampled by viewpoint |
| Draw calls | ≤ 150 typical, ≤ 220 worst | ≤ 90 typical | `renderer.info.render.calls` |
| GPU texture allocation | ≤ 256 MB | ≤ 96 MB | texture inventory × mip/format estimate; browser tooling cross-check |
| Initial transferred 3D assets | ≤ 20 MB compressed | ≤ 8 MB | resource timing/network log |
| Loaded pilot tiles | 1 active + bounded preload set | 1 active, minimal preload | TileManager event log |
| Frame rate | 60 FPS target; 45 FPS 1% low in saved views | 30 FPS target | 30-second fixed-route benchmark after warm-up |
| Initial interactive model | ≤ 5 s on defined broadband profile | ≤ 8 s | navigation timing + first rendered asset marker |

Cap device pixel ratio and disable/reduce shadows on constrained devices. KTX2/Basis, Meshopt/Draco, atlases, merging, and instancing are optimization candidates only after baseline metrics identify the bottleneck.

## Dependency-aware roadmap

`M0`–`M4` are complete for the canonical pilot. The low-fidelity portions of M7, M9, and M10 have also been exercised: grounded urban systems render, the GLB loads from a manifest with viewpoints/attribution, and fixed-view browser samples are recorded. M5–M6 remain the gate before any evidence-refined building or high-detail work.

| Milestone | Goal | Inputs | Outputs | Depends on | Model | Acceptance |
| --- | --- | --- | --- | --- | --- | --- |
| M0 Environment ready | Prove Blender/web toolchain | repository bootstrap | setup audit and fixtures | — | Luna | Already complete; do not repeat without a failure. |
| M1 Boundary + pilot | Fix reproducible scopes and choose benchmark | BCDA/plan evidence, OSM, candidate metrics | working/pilot GeoJSON, comparison | M0 | Sol | Boundaries versioned and classified; pilot dimensions/reason recorded. |
| M2 Geographic ingestion | Robustly import geographic entities | cached OSM extract, polygons, source registry | raw cache, normalized buildings/roads/paths/open space, coverage report | M1 | Sol | Multipolygons/holes/parts and provenance tests pass; refresh diff is reviewable. |
| M3 Coordinate transform | Enforce one metric coordinate contract | EPSG:4326 source, EPSG:32651, origin | tested transform module and metadata | M1 | Terra | Known invariants and local direction/scale tests pass; no degree math downstream. |
| M4 Real-data Blender prototype | Prove normalized geometry reaches Blender | M2/M3 subset, existing helpers | massing `.blend`, aerial render, GLB, metrics | M2, M3 | Terra | ≥10 real footprints render/export/re-import with evidence properties. |
| M5 Reference database | Store licensed/rights-reviewed references and matches | source registry, target building list | reference metadata files and matching workflow | M1 | Sol | Every accepted image has rights/provenance/hash/target; rejected candidates are recorded. |
| M6 Coverage system | Measure aspect gaps | M5 references, building orientations | per-building coverage records and research queue | M5 | Terra | Ratings are reproducible; duplicates do not inflate coverage. |
| M7 Pilot procedural reconstruction | Generate the urban base | M2–M6, asset library | roads, paths, buildings, vegetation/furniture, tile scene | M4, M6 | Sol | Full pilot base regenerates; systems use instances/shared materials; seams/metrics pass. |
| M8 First refined building | Validate evidence-driven recognition | Tier candidate, coverage, base asset | Tier A/B override, QA renders, discrepancy log | M6, M7 | Sol | Recognizable from agreed views; all claims classified; no unsupported hidden detail. |
| M9 Pilot web runtime | Evolve viewer to manifest/runtime | pilot GLBs, tile manifest, budgets | World/Tile/Asset/LOD shell and bounded orbit/fly | M7 | Sol | Manifest loads, attribution visible, viewpoints work, no critical errors. |
| M10 Pilot benchmark | Turn provisional budgets into evidence | M9, named desktop/mobile profiles | repeatable route results and revised budgets | M9 | Luna | FPS/draw calls/triangles/transfer/memory captured for fixed views/routes. |
| M11 Whole-BGC skeleton | Generate low-fidelity city coverage | working boundary, hardened ingestion/generators | Tier C tiles, completeness report | M7, M10 | Sol | Hundreds of entities if available; full boundary processed; gaps explicit. |
| M12 Spatial streaming | Load/unload city working set | M11 tiles/manifests, revised budgets | streaming, cache/disposal, seam handling | M11 | Sol | Long traversal has no duplicate/leaked assets or visible systemic seams. |
| M13 City-scale benchmark | Validate scale | M12, fixed routes/devices | stability/performance report and tuned limits | M12 | Luna | 10-minute route remains within revised memory/FPS thresholds. |
| M14 Pilot high-fidelity refinement | Improve selected Tier A/B assets | coverage gaps, QA discrepancies | refined pilot assets/LODs | M8, M10 | Sol; Astra only for individually justified ambiguous visual tasks | Improvements pass fixed-view QA and budgets; unsupported details remain labeled. |
| M15 Progressive expansion | Refine by value and evidence | city skeleton, tier scores, user priorities | additional reviewed blocks/buildings | M13, M14 | Sol | Each increment has coverage, provenance, QA, LOD and performance evidence. |

## Model allocation

- **Luna:** status, logs, artifact existence, fixed benchmark collection, routine re-import checks.
- **Terra:** deterministic transforms, normalization utilities after architecture is fixed, batch export, schema validation, simple viewer changes.
- **Sol:** source/coordinate architecture, entity resolution, multipolygon/tile logic, generator design, runtime/LOD/streaming, difficult debugging.
- **Astra:** only later, for a specific Tier A visual ambiguity or iterative reference-vs-render judgement that demonstrably exceeds Sol. It is not needed for this phase, ingestion, mass generation, or ordinary scripts.
