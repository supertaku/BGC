# M12 Runtime Report

Status: **PARTIAL**. The spatial runtime, caching, LOD switching, fallback, build, and automated gates pass. A stable foreground FPS comparison remains to be captured because the automated browser throttled `requestAnimationFrame`.

## Runtime design

The existing 94-tile world manifest remains authoritative. Each tile now has an explicit `UNREQUESTED`, `PRELOADING`, `READY`, `ACTIVE`, `CACHED`, or `ERROR` state plus bounds, distance, byte size, request count, readiness, and last-used time. Evaluation runs every 150 ms from `useFrame`; camera motion itself stays in mutable Three.js objects and refs.

The initial rings are 500 m active, 650 m deactivate, 750 m preload, and 1,000 m retention. With 250 m tiles this keeps approximately two tile layers visible, fetches another layer before entry, and leaves a 150 m activation/deactivation gap. Loaded scenes stay mounted and hidden, retaining Three/Drei's loader cache. The full 15.28 MB tile set does not justify hard memory eviction.

The seven registry assets use a custom split-file LOD manager: preload at 360 m, activate at 180 m, and restore LOD2 beyond 230 m. This preserves tile-owned LOD2 meshes and avoids repackaging solely to use `THREE.LOD`. No position or scale jump was observed.

## Measured runtime state

| Scenario | Active tiles | Requested tiles | Tile bytes |
| --- | ---: | ---: | ---: |
| Whole-BGC aerial | 22 | 43 | 9,460,572 |
| High Street | 21 | 40 | 8,509,244 |
| North | 22 | 43 | 9,460,572 |
| South | 22 | 43 | 9,460,572 |
| South street | 22 | 41 | 7,341,828 |

Average active tiles are 21.8 and the peak is 22. Browser QA observed zero repeated requests. ALL_LOADED activated all 94 tiles and retained the M11 fallback. High Street starts with a 71,368-byte interaction index, 8,509,244 tile bytes, and 298,172 bytes for the seven nearby preloaded LOD1 files, for 8,878,784 bytes. Expanding from that state to every tile adds 6,773,036 tile bytes.

The M11 foreground baseline remains 156.69 mean FPS aerial, 167.90 High Street, and 159.30 south street. The new automated browser run was heavily background-throttled and is not reported as comparable FPS evidence. A dynamic High Street render snapshot recorded 104 calls, 62,356 triangles, 94 geometries, and zero textures, but these are a state sample rather than a complete six-scenario benchmark.

## Gate

- Deterministic sidecars and index: PASS
- Preload, hysteresis, cache, and zero repeated fetches: PASS
- Seven LOD1 switches and no observed flicker: PASS
- Dynamic and ALL_LOADED modes: PASS
- Production build and regression tests: PASS
- Stable foreground performance benchmark: PARTIAL

Machine-readable evidence is in `data/reports/m12-runtime.json`.
