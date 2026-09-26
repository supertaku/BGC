# M19D.1 Explore controls and Walk street awareness

Status: **READY_FOR_USER_VALIDATION**. This is a manual-feedback corrective pass on M19D. The earlier M19D evidence remains in `M19D_RUNTIME_STABILITY_REPORT.md`.

## Baseline and cause

- Branch and starting HEAD: `main`, `16666cf9e39a99d30241380f55eb88fbac713248`; starting worktree clean.
- Installed: Three 0.180.0, R3F 9.7.0, Drei 10.7.8, three-stdlib 2.36.1.
- Rendering path: Canvas → WorldRuntime → NavigationController → Drei MapControls in `INSPECT`; PointerLockControls only in `WALK`.
- Drei selected `events.connected` before the Canvas when `domElement` was omitted. The browser debug probe identified `events.connected` as `OTHER` and the explicit MapControls target as `CANVAS`.
- The previous inline `onStart` handler changed identity on every React rerender. Drei's MapControls effect depends on that handler and disconnects/reconnects its listeners when the identity changes. This provides a concrete mechanism for dragging to stop mid-interaction. Stable callbacks now retain the connection, and the Canvas is passed explicitly.

## Implementation

Explore explicitly maps left to pan, middle to dolly, right to rotate, wheel to zoom. Pan, rotation, zoom, ground-plane panning, and damping are explicit. MapControls owns the Canvas context menu; no page-wide suppression was added. Selection still requires primary button and at most 5 px movement. Manual control cancels the pending or active focus transaction; consumed sequence IDs prevent restart. The target clamp only writes when out of bounds.

Tile sidecars now contain only named road/path centerline segments from the existing normalized OSM snapshot. The generator clips source centerlines against each 250 m tile, handles LineString, MultiLineString, and GeometryCollection lines, converts north to runtime `-z`, preserves IDs/aliases, and sorts output deterministically. No OSM snapshot or visible geometry changed. All 94 sidecars regenerate byte-identically on a second run.

`StreetLocator` samples every 250 ms in Walk, searches sidecars within 125 m of the camera, skips stationary resampling when the candidate set is unchanged, caps acceptable road/path distance at 30 m, and requires 4 m improvement before switching from a still-eligible street. It publishes React state only when the street ID changes. The label is above Walk help; no label appears when no named way qualifies. The source label is **verified geographic data** from OSM, subject to OSM's own accuracy.

## Automated evidence

| Check | Result |
| --- | --- |
| Build, lint, product, GLB metadata, instancing | PASS |
| Python unittest suite | 55 PASS (excluding pytest-only assessor) |
| Python assessor pytest | 2 PASS |
| New street logic/configuration tests | PASS |
| Sidecar geometry/data validation | 1,470 road and 103 path segments; 87 tiles with named ways; 0 invalid identity/geometry records |
| Repeated left drag browser probe | 2 Canvas pointer downs, 2 MapControls starts/ends, camera moved, pan changes recorded, 0 target clamps |
| Right drag browser probe | NOT_AVAILABLE: browser automation exposes only left-button drag |
| Search scripted run | 8 requests, 8 starts/completes, 0 cancels, 0 zero-visible events, 0 repeated tile requests, 0 LOD gaps |
| Tour scripted run | 7 requests, 7 starts/completes, 0 cancels, 0 zero-visible events, 0 repeated tile requests, 0 LOD gaps |
| Walk locator sample | 143 nearby clipped segments at spawn; 250 ms cadence, no label at a spawn 21.45 m from the nearest named road |

The automated pointer probe establishes input delivery and camera movement, not mouse feel or visual correctness. Right rotation/tilt and Walk label behavior in real use remain **AWAITING_USER_TEST**. M19D and readiness for M19E remain pending that validation.

## Manual validation checklist

1. Explore: left-drag empty map area to pan; right-drag horizontally to rotate and vertically to tilt; scroll to zoom.
2. Repeat left and right drags across BGC; confirm the city stays visible and right drags do not select buildings.
3. Search several distant buildings; confirm one smooth focus per request.
4. Enter Walk and confirm pointer lock. Walk named streets and cross intersections; check that the label appears above Walk help and changes only after clearly entering another street.
5. Continue along one street across a tile boundary; confirm the label stays stable. In an area without a nearby named way, confirm no street is invented.

**M19D.1: READY_FOR_USER_VALIDATION. Ready for M19E: NO.**
