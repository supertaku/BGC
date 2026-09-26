# Decision log

## 2026-09-10 — Synthetic bootstrap only

Use deterministic synthetic geometry to validate the pipeline before acquiring BGC data or producing real buildings.

## 2026-09-10 — Metre-scale local frame

Use one scene unit per metre and plan a projected local origin for geographic inputs. Rely on Blender's glTF export conversion from Z-up to glTF/Three.js Y-up.

## 2026-09-10 — Generated artifacts are ignored

Commit scripts and small source inputs. Ignore reproducible `.blend`, PNG, copied viewer GLB, and build outputs to avoid repository churn.

## 2026-09-10 — Versioned project scope, not a claimed legal boundary

Store the current BGC query extent in `data/geographic/bgc-working-boundary.geojson` and label it estimated. Available authoritative material establishes a master plan and approximate development area but did not provide a reusable machine-readable legal polygon.

## 2026-09-10 — High Street central core is MVP-A

Use the approximately 494 × 419 m polygon spanning the central High Street corridor. Measured OSM metadata provides the best combined pedestrian, vegetation, furniture, retail, road, and mixed-building benchmark; higher raw imagery counts alone do not determine the choice.

## 2026-09-10 — EPSG:32651 and a fixed BGC origin

Project WGS84 input with WGS 84 / UTM zone 51N, then subtract longitude 121.050972, latitude 14.550806 as the fixed engineering origin. Treat altitude separately and retain Blender metre/Z-up and exporter-owned glTF Y-up conversion.

## 2026-09-10 — JSON/GeoJSON through MVP-A

Use versioned files plus JSON Schema and source hashes. Defer SQLite until query/edit friction is measured; do not introduce PostGIS for the MVP.

## 2026-09-10 — Evidence is field-level

Classify observations as `VERIFIED_GEOGRAPHIC`, `VERIFIED_PHOTOGRAPHIC`, `INFERRED`, `ESTIMATED`, `PROCEDURAL`, or `UNKNOWN`. Missing evidence must remain visible and cannot be upgraded by normalization or generation.

## 2026-09-10 — Per-tile Blender generation

Plan generated 250 m tile `.blend` files, small shared asset libraries, and separate manual landmark overrides. Do not use one master city `.blend`.

## 2026-09-10 — Bounded orbit/fly first

Evolve the integration viewer toward bounded orbit/fly navigation with saved viewpoints. Defer first-person walking, complex collision, and guided-tour orchestration until the pilot's scale and runtime are stable.

## 2026-09-10 — Maintained geospatial libraries

Use pinned pyproj 3.7.2 for EPSG transforms with `always_xy=True` and Shapely 2.1.2 for relation assembly, validity repair, clipping, buffering, precision, and union. The former hand-coded UTM routine is removed from the production coordinate path.

## 2026-09-10 — Full pilot entities, diagnostic surfaces

Normalize all in-scope building outlines/parts, roads, pedestrian ways, open spaces, and POIs from one immutable snapshot. Keep per-feature centerlines and source IDs canonical, but dissolve derived road/path/open-space surfaces for the Blender export to avoid overlapping coplanar geometry and excessive draw calls.

## 2026-09-10 — Height evidence is visible

Use blue for explicit OSM `height`, amber for the existing `building:levels × 3.2 m` estimate, and rose for procedural fallbacks. OSM presence is geographic provenance, not an independent survey. Do not alter suspicious heights merely to improve the skyline.

## 2026-09-10 — Reference discovery remains metadata-only

The M5-lite proof of concept retrieves up to two Wikimedia Commons metadata candidates for three pilot buildings and downloads zero images. Mapillary remains `BLOCKED_CREDENTIALS` without a token and does not block the geographic pipeline.

## 2026-09-11 — Persistent JSON canonical entities for M5

Keep JSON/GeoJSON for the 31 canonical pilot building/structure entities and two complex records. Persist project-owned `bgc_*` IDs plus source mappings. SQLite remains a future option when measured query/edit friction justifies migration; PostgreSQL/PostGIS is unnecessary.

## 2026-09-11 — Containment links parts; ambiguity does not merge identities

Associate a building part automatically only at near-complete geometric containment or through an explicit source relation. Merge the unnamed Mariano K. Tan Center duplicate outline only because containment and a shared building part jointly support one entity. Keep the nested Bench footprint as a reviewable child and the two duplicate `B:3` labels as separate `REVIEW_REQUIRED` entities.

## 2026-09-11 — Rights and identity decisions are independent

A reference can have reusable rights but an unresolved entity match, or a confirmed identity but research-only media. Commons licenses are normalized per file. Official-site imagery defaults to `RESEARCH_ONLY`. Unknown or malformed terms become `REVIEW_REQUIRED`.

## 2026-09-11 — Central Square is the first reconstruction-package target

Recommend Central Square because it has confirmed identity, explicit geographic height, three resolved parts, official factual evidence, and two rights-reviewed Commons records. This is a package/coverage decision, not authorization to begin detailed modeling. W Global Center is the backup.

## 2026-09-14 — Central Square is an independent LOD1 asset

Generate Central Square from its validated reconstruction package into an independent editable `.blend` and runtime GLB, then substitute it for only the four original Central Square OSM extrusion features during pilot generation. Preserve LOD2 regeneration through `--central-square-lod2`. Use simple Principled metallic/roughness materials, export evidence metadata as glTF extras, omit unsupported east/roof/portal detail, and keep fixed diagnostic cameras separate from the runtime GLB.

## 2026-09-14 — Versioned reconstruction contract and external evidence source

Use `schema_version: "1.0"`, a committed Draft 2020-12 JSON Schema, and dependency-free early/cross-file validation. Store only compact identity/component/observation metadata in GLB extras; canonical evidence, rights, conflicts, and unknowns remain under `data/`.

## 2026-09-14 — Semantic authoring, explicit runtime optimization

Keep Central Square's 25 logical authoring meshes. Merge only the four same-role north bands and five same-role south columns in runtime, retaining source component ID arrays. This reduces runtime meshes/draw calls from 25 to 18 without changing 356 triangles or the five QA renders. Defer Geometry Nodes and GPU instancing until a larger repeated pattern demonstrates a benefit.

## 2026-09-14 — Registry-driven reconstructed asset integration

Resolve approved builders, replaced source features, LOD assets, lifecycle state, metrics, and merge policies from `data/assets/buildings.json`. The pilot no longer imports a Central Square path or source-ID set directly.

## 2026-09-14 — M10 configured polygon batch

Keep reconstruction schema 1.0. Add one winding-aware polygon-edge facade primitive and express all five M10 targets as package configuration, with no target-specific Python builder. Preserve semantic edge components in authoring and merge each same-material band family for runtime. Integrate configured targets from validated standalone GLBs through the asset registry. Defer GPU instancing and streaming because measured pilot cost remains low.

## 2026-09-15 — Whole-city fixed grid and merged tile runtime

Generate M11 as deterministic 250 m local-meter tiles, with canonical building ownership by centroid and contained parts following their outline. Subtract part footprints from parent outlines before extrusion to avoid duplicate massing. Keep individual objects during authoring, merge runtime geometry by tile/material, and preserve entity lookup in the manifest sidecar. Load all 94 tiles initially because the measured 15.58 MB scene remains smooth on the current desktop; defer distance streaming until scaling evidence requires it.

## 2026-09-15 — Visibility-first dynamic tile runtime

Use the M11 world manifest with explicit runtime states and 500/650/750/1,000 m active/deactivate/preload/retention rings. Retain fetched GLBs in the Drei loader cache and mounted scene graph because the complete city is only 15.28 MB. Treat ALL_LOADED as a supported fallback. Do not hard-evict until measured memory pressure justifies network refetch risk.

## 2026-09-15 — Registry-driven split-file landmark LOD

Use a custom manager for seven separate LOD1 GLBs and tile-owned merged LOD2 groups. Preload at 360 m, activate at 180 m, and restore beyond 230 m. This preserves existing packaging and provenance rather than restructuring assets solely to fit `THREE.LOD`.

## 2026-09-15 — Sidecars separate interaction from rendering

Keep merged tile GLBs for rendering. Generate compact per-tile footprint/environment sidecars for nearby 2D collision and picking, plus a 263-record named/detailed global search index. Runtime spatial work stays in local project metres; latitude/longitude projection remains offline.

## 2026-09-15 — Source-grounded instanced environment

Reuse the immutable normalized OSM POIs and add no procedural filler because 452 mapped objects provide a useful first layer. Assign every object to one M11 tile and instance by tile plus asset type. Generic geometry represents category and mapped position, not photographed appearance.

## 2026-09-26 — Evidence-labelled visual-detail preview, promotion deferred

Derive High Street paving borders and sparse generic park/furniture detail from the pinned OSM path/park polygons. Keep inferred widths and new object positions explicit in the package and M20 ledger. Use tile-clipped surface batches and instanced furniture without regenerating successful GLBs. Enable only through `detail=1` while walking baseline measurements are unstable. Preserve normal LOW and all approved landmark assets. Do not promote new facades, signs, art, or grade transitions without target-level evidence and validation.
