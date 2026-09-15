# Interactive BGC Runtime Report

Phase: **PARTIAL**

Combined milestone: **M12-M14 Interactive BGC Runtime**

The project can now reasonably be described as an interactive browser-based 3D representation of BGC with geographic massing, seven selected detailed landmarks, spatial tile/LOD management, first-person controls, building interaction, a guided tour, and lightweight mapped urban context. The PARTIAL rating is limited to foreground pointer-lock and FPS validation, not a known build or data failure.

## Delivered

- Dynamic 94-tile runtime with explicit states, distance rings, hysteresis, loader retention, and ALL_LOADED fallback
- Seven automatic LOD1/LOD2 substitutions without observed flicker or positional jumps
- Inspect, Walk, and Tour navigation states with delta-time movement and nearby-footprint collision
- Footprint selection, 263-entry local search, and a seven-stop landmark tour
- 452 mapped street objects in tile/type instanced groups with OFF, LOW, and FULL quality
- Optional instrumentation for tiles, LODs, bytes, requests, camera, calls, triangles, geometries, textures, and FPS

## Preserved baseline

The implementation preserves 94 tiles, 6,982 canonical buildings, 306,596 LOD2 triangles, 15,282,280 tile GLB bytes, seven LOD1 assets, the asset registry, metadata, coordinate system, and prior reconstruction artifacts. No geography or LOD1 building was regenerated.

## Validation assessment

Lint, production build, and 49 automated tests pass. Browser QA verified dynamic and all-loaded tile modes, zero repeated tile requests, LOD changes, search/focus, details, tour progression, and environment lifecycle. Synthetic automation could not establish a trusted pointer-lock session and heavily throttled frame callbacks, so the combined gate remains PARTIAL pending a short foreground manual benchmark.

The next milestone should be **M15 foreground runtime validation and navigation hardening**: run the six requested scenarios in a visible production browser, validate real pointer lock/collision at representative buildings, and record comparable FPS distributions. Use **SOL** for the remaining runtime edge cases; Astra is not required.

Machine-readable rollup is in `data/reports/interactive-bgc-summary.json`.
