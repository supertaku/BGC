# M11 — Whole-BGC Low-Fidelity Skeleton

Phase: **PASS**

Milestone: **M11 — Whole-BGC Low-Fidelity Skeleton**

## Boundary and dataset

The versioned project working boundary remains estimated information, not a legal boundary. It covers 4,723,913.01 m² with WGS84 bounds `[121.0400, 14.5370, 121.0602, 14.5630]`. The immutable 2026-09-14 snapshot came from the official OpenStreetMap map API in a deterministic 4 × 4 acquisition grid after public Overpass instances timed out. Source and query hashes are retained.

- Building outlines: 6,967
- Building parts: 154
- Canonical rendered buildings: 6,982
- Render volumes after part-aware outline subtraction: 7,120
- Named building features: 305
- Roads: 1,824
- Paths: 1,226
- Open spaces: 206
- Invalid/deferred geometry: 0 pipeline failures; 117 source review items

Height evidence is 295 `VERIFIED_GEOGRAPHIC` (4.14%), 77 `ESTIMATED` (1.08%), 6,749 `PROCEDURAL` (94.78%), and 0 conflicted. Height QA is **PARTIAL** because source height coverage is sparse. The automated queue contains 15 orphan parts and 102 part/parent height mismatches, all classified as `SOURCE_DATA_ISSUE`; no pipeline-error anomaly remains.

## Spatial generation

The fixed 250 m local-meter grid produced 94 stable centroid-owned tiles. Parts follow their containing canonical outline. Parent outlines are geometrically subtracted by associated part footprints before extrusion, preventing full-outline-plus-part duplicate massing while retaining uncovered outline residuals. Average density is 74.28 canonical buildings per tile. The largest tile is `tile_007_004` with 479 buildings and 430,704 bytes.

All 94 tiles passed Blender 5.2 generation and GLB export. Total LOD2 size is 15,282,280 bytes, with 306,596 triangles and 522 runtime nodes. The seven approved LOD1 assets remain separate and registered alongside tile-owned LOD2 availability. The viewer loads all tiles because measured cost is small enough; it hides the seven corresponding LOD2 groups and uses their LOD1 assets.

The representative `tile_004_007` comparison selected merged-by-material output: 8 meshes and 266,556 bytes versus 17 meshes and 273,916 bytes per-building, with the same 5,620 triangles. Canonical identity is preserved in the tile sidecar manifest.

## Runtime and QA

Measured on Chrome 152 at 1280 × 720, DPR 1.25, Intel Iris Xe:

| Scenario | Load | Mean FPS | Median FPS | p1 FPS | Calls | Triangles | Geometries |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Whole-BGC aerial | 1,733 ms | 156.69 | 156.25 | 91.74 | 557 | 310,388 | 566 |
| High Street | 789 ms | 167.90 | 163.93 | 100.00 | 233 | 147,684 | 239 |
| South street | 784 ms | 159.30 | 161.29 | 82.64 | 394 | 238,092 | 403 |

Initial whole-city transfer including seven LOD1 assets is 15,580,452 bytes. No textures are active. Geographic QA is **PASS** at district scale: the working-boundary silhouette, tower core, major road network, dense perimeter fabric, open-space pattern, and High Street axis are legible. This is procedurally materialed massing, not verified architectural appearance.

Production build: **PASS**. Automated tests: **44 PASS**. Dominant city-scale bottleneck: draw calls from 94 tile assets plus seven detailed assets. Recommended next milestone: targeted height-evidence cleanup and selective LOD refinement, using **TERRA** for deterministic audit/generation with **SOL** only for difficult part semantics. Astra required next: **NO**.
