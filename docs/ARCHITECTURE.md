# Architecture

## Grounded pilot pipeline

```text
immutable Overpass JSON
  -> Shapely/pyproj normalization and QA
  -> local-metre GeoJSON
  -> Blender Python/bpy diagnostic generator
  -> .blend + five QA renders + GLB
  -> GLB re-import metrics
  -> manifest-driven Next.js/R3F viewer
```

`scripts/geography/fetch_osm.py` acquires immutable snapshots for an arbitrary boundary. `normalize_osm.py` is the canonical parser/topology/CRS boundary. `blender/scripts/scene_tools.py` remains the reusable deterministic geometry layer; `generate_bgc_pilot.py` adds real footprints, dissolved road/path/open-space surfaces, batched vegetation/furniture, fixed cameras, and export. The synthetic generators remain regression fixtures.

## Reconstruction pipeline

```text
OpenStreetMap / GIS + licensed photographic references
    -> entity resolution
    -> structured reconstruction database
    -> procedural Blender generation
    -> reference-based refinement
    -> visual QA
    -> GLB / spatial assets
    -> Three.js
```

## M8 reusable reconstruction boundary

```text
versioned package + canonical evidence
  -> dependency-free contract/cross-file validation
  -> target-specific architectural interpretation
  -> shared materials + metadata + facade coordinates + QA cameras
  -> semantic authoring .blend
  -> explicit runtime merge policy
  -> GLB metrics/metadata validation
  -> building manifest + asset registry
  -> registry-driven pilot integration
  -> fixed production browser benchmark
```

`blender/framework/` owns reusable mechanics. Building directories own architectural interpretation. Authoring assets retain logical components and QA helpers; runtime assets contain only required nodes/materials/compact extras. Canonical evidence never migrates into Blender or GLB.

The first grounded pilot is implemented end-to-end. It deliberately stops before facade reconstruction. Wikimedia discovery is metadata-only; Mapillary is a credential-safe blocked boundary. Future modules remain identity resolution, accepted reference coverage, evidence-driven refinement, tiling/streaming, and production benchmarking.

Canonical design details now live in:

- `docs/BGC_SCOPE.md`
- `docs/DATA_ARCHITECTURE.md`
- `docs/RECONSTRUCTION_PIPELINE.md`
- `docs/MVP_PLAN.md`
- `docs/RISK_REGISTER.md`

## M5 evidence architecture

```text
pilot-buildings.geojson
  -> resolve_entities.py
  -> pilot-entities.json + aliases.json + entity review queue
  -> batched/cached Wikidata enrichment
  -> two-stage Commons discovery and rights enrichment
  -> deduplicated references + rights/reference review queues
  -> observations + precedence/conflicts
  -> coverage + readiness reports
  -> reconstruction package
```

JSON/GeoJSON remains the canonical M5 store: the pilot relationships fit comfortably, diffs are inspectable, and there is no measured concurrent-query need for SQLite yet. Project IDs are append-only and source mappings are persisted; OSM IDs remain source identifiers. Raw API responses live under `data/cache/`, full-resolution imagery stays external unless separately rights-approved, and all ambiguous decisions enter `data/review/`.

## Coordinate strategy

- Use metres. Blender scene unit scale is `1.0`, so one Blender unit represents one metre.
- Source latitude/longitude is angular data on an ellipsoid and must not be used directly as ordinary scene coordinates. Degree distances vary by latitude, numerical magnitudes are unsuitable for real-time rendering, and altitude is not represented consistently by a raw longitude/latitude pair.
- Project EPSG:4326 geographic input with pyproj 3.7.2 to EPSG:32651 (WGS 84 / UTM zone 51N), then subtract the fixed origin at longitude 121.050972, latitude 14.550806. Shapely 2.1.2 owns polygon assembly, validity, clipping, buffering, precision, and union. Store the source/projected CRS, origin, source hash, and precision with processed data.
- Use a local engineering frame conceptually as east, north, up in metres. Convert at the ingestion/export boundary rather than scattering coordinate swaps through modeling code.
- Blender is right-handed and Z-up. glTF is right-handed and Y-up; Blender's glTF exporter performs the axis conversion. Three.js is right-handed and Y-up, so a correctly exported GLB should be loaded without an ad-hoc rotation.
- Treat altitude separately from horizontal projection. Record the vertical datum or explicitly mark heights/elevations as estimated. Subtract the chosen local origin elevation before scene generation to keep values near zero.
- Plan a 250 m EPSG:32651 tile grid indexed from the fixed origin. Buildings are centroid-owned and unsplit; linear/area networks are clipped with deterministic seam overlap. Do not implement full streaming until pilot manifests and browser benchmarks exist.

## Asset and runtime direction

- Generate disposable per-tile `.blend` files from data; keep reusable asset libraries and manual landmark overrides separate. Avoid a monolithic master file.
- Use LOD0–LOD3, preserving evidence-backed detail near the camera and reducing to silhouette/cluster proxies at distance.
- Evolve the viewer around a typed world/tile manifest, then `WorldManager`, `TileManager`, `AssetLoader`, `LODManager`, `NavigationController`, and `PerformanceMonitor`. Keep per-frame state out of React state.
- Start navigation with bounded orbit/fly plus saved viewpoints. Defer walking/physics until scale and collision proxies are trustworthy.

## M10 batch reconstruction

```text
m10-batch.json -> package validation -> configured polygon builder -> per-target GLB validation -> asset registry -> registry-driven pilot import -> browser metrics
```

Batch execution isolates target failures and supports fail-fast, continue-on-error, and exact-target retries. Existing custom builders remain supported; configured M10 assets integrate from their already-optimized standalone GLBs. Canonical evidence remains outside Blender.

## M20–M22 visual-detail preview

`scripts/visual_detail/build_visual_detail.py` derives a compact, tile-clipped JSON package from the pinned path and park polygons. `PublicRealmManager` renders merged surfaces per tile/material and pooled furniture instances from visible owner tiles. Canonical evidence and review decisions remain in the M20 ledger. The preview is enabled only by `detail=1`; it allocates no geometry in the default LOW experience. Promotion requires stable walking benchmarks and completion of the remaining visual/navigation gates. The existing GLBs, approved LOD1 registry, collision and navigation data are unchanged.

## M21R–M22R refinement

`data/config/surface-heights.json` is the height contract. The tile Blender generator reads it directly; `build_visual_detail.py` produces the checked runtime copy. Version 2 detail data lives under `web/public/world/detail/` and is fetched once only for opt-in detail modes. `PublicRealmManager` selects active tile records; `SurfaceDetailLayer` merges per tile/material; `StreetscapeInstanceLayer` pools instances per category. Geometry is disposed by the owning layer. Generated inputs carry hashes; per-record source and grounding are mandatory.

The generator resolves surface intersections against highest PATH, OPEN_SPACE, ROAD, then GROUND support. Mapped environment sidecars have priority over inferred candidates. All normalized paths, roads and building footprints enter exclusion checks; furniture may occupy only the owning plaza edge strip. Reports keep engineering results separate from user-owned appearance acceptance.

## M23 spatial landmark and terrain preview

`scripts/m23/prepare.py` retains evidence and resolves canonical building-part ownership. `build.py` produces indexed surface meshes, primitive instances, signage/art anchors and local ground triangles. Detailed provenance remains in `data/visual_reference/features`; compact runtime JSON is loaded only with `detail=m23`. `M23Manager` batches all active geometry by material and primitive kind, applies distance hysteresis, caches fetches and disposes GPU resources on unload. The existing seven approved LOD1 assets remain authoritative.

Preview-only tile variants isolate replacement fallback meshes. A fallback hides only after its matching package is loaded and active; failed detail fetches leave the base geometry visible. The base city GLBs and default LOW experience are unchanged. `GroundSampler` supplies barycentric local terrain height to Walk, with deterministic priority and removal on package unload. Blender consumes the same generated meshes and instances for GLB exports and fixed-camera QA. See the M23 reports for evidence gaps and pending user acceptance.
