# M21R–M22R acceptance

**PARTIAL. Preview only.** Automated implementation gates pass; subjective appearance is AWAITING_USER_TEST. Performance acceptance is not established by throttled browser runs. M20 remains partial and M23 is deferred.

Production preview: http://127.0.0.1:3001/?view=bgc-high-street&mode=inspect&detail=1

The machine report is [visual-detail-acceptance.json](../data/reports/visual-detail-acceptance.json). Current observations are [m21r-browser-validation.json](../data/reports/m21r-browser-validation.json); historical M21 observations remain separate and are not reused for acceptance.

## Engineering

Browser Search completed 8/8 targets and Tour 7/7 stops. Walk completed with no zero-visible events, repeated tile requests, runtime errors or LOD gaps and stopped at measurement end (camera comparison tolerance 0.051 m, matching the runtime display rounding). Seven LOD1 assets loaded. Detail OFF made zero package requests; ON made one.

Production build, lint, product-state checks, metadata, existing GLB instancing fixture, public-realm schema/lazy-cache checks, deterministic semantic verification, 63 Python tests, coordinate checks and processed-data checks pass. The instancing fixture checks the existing shared GLB; the detail renderer independently uses InstancedMesh batches by category. No texture assets or materials are added. Bench geometry uses 48 triangles.

Reproduce with `.venv/Scripts/python.exe scripts/visual_detail/build_visual_detail.py`, `scripts/visual_detail/verify_visual_detail.py`, and `scripts/visual_detail/report_refinement.py`. Run `npm run build`, `npm run lint`, `npm run verify:product`, `npm run verify:metadata`, `npm run verify:instancing`, `npm run verify:street-controls`, `npm run verify:public-realm` from `web`. Python: `.venv/Scripts/python.exe -m pytest tests --basetemp=.pytest_tmp_m21r_new -q`.

## Performance protocol

Use the same foreground Chrome tab, viewport, DPR, LOW quality and fixed starting viewpoint. Reload between runs; alternate three OFF and three ON runs for Inspect and Walk. Parameters: `debug=1&benchmark=1&quality=LOW&detail=0` or `detail=1`; Walk adds `mode=walk&benchmark_walk=1`. Movement starts at benchmark warmup and stops at the measurement deadline. Counters are captured with the last completed render before subsequent movement. Reject background/unfocused, 900 ms frame contamination, changing viewport/DPR, incomplete Walk and runtime-error runs. Compare medians across valid runs; investigate >15% median/p1 degradation, likely fail >25%. The retained invalid 1 FPS runs provide no FPS acceptance evidence.

## Manual inspection — all AWAITING_USER_TEST

- High Street aerial: visible paving and park borders, no z-fighting.
- Walking level: parallel benches and planters, believable lamp spacing, clear circulation.
- Track 30th: trees off paths, no mapped-tree duplicates, clear planters.
- Intersection: visible crossing above its actual PATH support, no floating appearance.
- Tile boundary: continuous surfaces, no duplicated instances.

Keep all four diagnostics: `detail=0`, `detail=1`, `detail=surfaces`, `detail=instances`. The default absent parameter is OFF. No whole-world Suspense was introduced.

Ready for M23: **NO — pending user validation and remaining acceptance gates.** Next milestone after user PASS is M23 — Landmark Facade, Signage and Identity Expansion. Do not begin automatically.
