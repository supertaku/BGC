# M19D runtime stability report

Status: **READY_FOR_USER_VALIDATION**. Automated implementation passed; all manual 3D interaction and visual checks are **AWAITING_USER_TEST**.

## Repository baseline

- Branch: `main`; starting and current HEAD: `0e8ac857b9077b7393706063ca9278918848769c`.
- Starting worktree was dirty: five `docs/remaining_phases/` files deleted and `web/next-env.d.ts` modified by a Next development type path. These changes predated M19D and were not intentionally reset. M19D code and reports remain uncommitted.
- Node 22.20.0; npm 11.18.0; Three.js 0.180.0; R3F 9.7.0; Drei 10.7.8; Next.js 16.3.4.

## Root causes and changes

Before M19D, `SceneViewer` placed the entire `WorldRuntime` beneath one `Suspense` boundary. A newly mounted `useGLTF(tile.url)` or `useGLTF(asset.url)` could suspend that shared subtree, including navigation, environment, and previously loaded city content. Each tile and landmark now has its own `Suspense` and error boundary. A failed tile GLB is marked `ERROR`; a failed detailed GLB retains generic LOD2. Sidecar failure leaves tile rendering intact, though picking, collision, and environment metadata for that tile are unavailable.

Tile state previously equated `ACTIVE` with visible content and hid the old neighborhood before a new one was ready. The manager now tracks desired, ready, active, and visible sets separately. It retains the last visible set until a ready replacement exists. Existing 500/650/750/1,000 m hysteresis radii remain. Stream anchors use the Explore target, Walk camera, or pending Search/Tour center; a camera secondary anchor is included only within 650 m of the primary, avoiding aerial request expansion. Temporary Explore target bounds come from the 94 tile coverage bounds with 350 m padding. `temporary_bgc_navigation_bounds = true`; this is a navigation constraint, not a verified legal boundary.

The seven LOD1 assets now report readiness after GLTF resolution and harmonization. Generic LOD2 remains visible until LOD1 is ready and active, then returns on deactivation. The runtime counts logical handoff gaps. Search and Tour preload their target tile and optional LOD1, and a camera transaction starts only after the target tile's GLB is ready. Sequence IDs consume each request once, with cancellation on a newer request or MapControls start.

Explore uses the installed Drei `MapControls`. Its installed `three-stdlib` implementation maps left to pan, right to rotate, middle to dolly, and prevents the Canvas context menu. Building selection accepts only a primary-button click within 5 px. PointerLockControls mount only in Walk; Walk keys and lock are cleared on exit. The initial aerial camera fits the tile-derived extent using camera FOV and viewport aspect. Search/Tour camera distance fits entity bounds and height. The camera far plane and MapControls max distance permit narrow viewport framing; subjective composition remains a user check.

Debug-only `?debug=1` exposes `window.__BGC_STABILITY__` plus `data-stability` and `data-runtime` on the metrics panel. It tracks zero-visible intervals, tile requests and transitions, focus lifecycle, LOD readiness and gaps, and pointer-control mounts. No external analytics or public tile counters were added.

## Automated evidence

| Check | Result |
| --- | --- |
| Production build, lint, product state, GLB metadata, instancing | PASS |
| Python repository tests | 53 scoped `unittest` tests passed in `.venv`; 2 assessor `pytest` tests passed with system Python and workspace `--basetemp` |
| Pure tile traversal | 94 manifest tiles; 88 requested across six waypoints; 0 simulated zero-visible events; last-good handoff passed |
| Live Search stress, `?debug=1&stability_run=1` | 8 requests, 8 starts, 8 completes, 0 cancels, 0 zero-visible events, 0 repeated requests, 0 errors; final 18 visible tiles, 86 requested cumulatively |
| Live Tour stress, `?debug=1&tour=bgc-landmarks&stability_run=1` | 7 requests, 7 starts, 7 completes, 0 cancels, 0 zero-visible events, 0 LOD gaps, 0 repeated requests; final 30 visible tiles |
| Live scripted Walk, `?debug=1&navigation=WALK&benchmark_walk=1&benchmark=1&view=bgc-high-street` | 0 zero-visible events, 0 repeated requests, 0 errors; 1 Walk control mount; 26 visible tiles at benchmark capture |
| Seven LOD1 readiness and handoff logic | PASS; 7 assets ready and 0 live handoff gaps in the sampled runs |
| Streaming growth guard | PASS; final active/visible sets remained 18/18 in Search, 30/30 in Tour, 26/26 in Walk; no all-94 visible state |

The Walk benchmark produced mean 166.17, median 166.67, and p1 126.58 FPS, with 47 draw calls, 50,922 triangles, 63 geometries, and 0 textures at capture. **PERFORMANCE_CAPTURE_INVALID** for matched desktop comparison: the in-app viewport was 699×715 at DPR 1.25, not the required desktop reference viewport. The structural counters above remain useful. No M20 performance optimization was attempted.

## User validation

From `web/`, run `npm run dev` and open `http://localhost:3000/`. The production alternative is `npm run build` then `npm run start`. Keep quality at the default LOW.

All items below are **AWAITING_USER_TEST**:

1. Initial BGC framing; left drag pan; right drag rotate/tilt; wheel zoom.
2. Repeated Explore movement without a blank world.
3. Search several distant buildings and confirm one smooth focus each.
4. Run all Tour stops and check camera transitions.
5. Enter Walk and confirm pointer lock, WASD, sprint, collision, and a long walk across BGC without disappearing geometry.
6. Approach the seven detailed buildings and check visible LOD continuity.

Known later-scope limits: no regional context, mostly flat ground, Walk eye height about 1.7 m, no High Street elevation/stairs/ramps, low-fidelity roads and sidewalks, mostly generic LOD2 buildings, seven detailed LOD1 assets, and no mobile Walk controls. M19E may begin only after the user reports manual M19D results.
