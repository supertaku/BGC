# Visual detail acceptance

**Gate: not yet accepted. Preview only.** M20 evidence and an M21/M22 first detail layer are implemented. M23 new facade identity and art/signage are still open. The normal LOW default is preserved; enable the experimental layer with `?detail=1`. Use `detail=0`, `detail=surfaces`, or `detail=instances` for diagnostics. No new geometry is allocated when the preview is off.

Production build, lint, deterministic ownership/provenance checks, product-state/search/263 place-link checks, seven simulated LOD handoffs, street-control checks and the existing instancing fixture pass. The foreground High Street scene loads with the new layer and existing LOD1 assets. Full UI search/tour/manual walking regression remains open.

One matched LOW inspect pair measured: detail off 166.20 mean / 163.93 median / 144.93 p1 FPS, 60 calls and 56,988 triangles; detail on 166.30 mean / 163.93 median / 135.14 p1 FPS, 70 calls and 60,398 triangles. Both showed 24 visible tiles, 2 LOD1 assets and zero textures. The optimized layer adds 10 calls and 3,410 triangles at that camera. Its JSON package is about 29 KB and adds no texture assets.

Walking is inconclusive and prevents promotion. The first baseline had p1 140.85 FPS; detailed runs had 93.46 and 67.57 FPS. A later no-detail baseline also fell to 69.44 FPS. This drift prevents attribution to the new layer. Preserve every observation in [visual-detail-benchmark-observations.json](../data/reports/visual-detail-benchmark-observations.json), including failed runs. The scripted walk continues after measurement; renderer counts read later are not synchronized benchmark-end values.

Grounded: source polygons and existing approved assets. Inferred: visual border widths and sparse generic furniture. Deferred: stable walking measurements, complete visual and navigation regression, new landmark facade packages, requested generalized stair/ramp/median builders, rights-reviewed logos and art. Rejected: speculative grade changes and unevidenced logo/art placement. No acceptance claim is made until the open gates pass.

Reproduce data: `.\.venv\Scripts\python.exe scripts/visual_detail/build_visual_detail.py`, then `scripts/visual_detail/verify_visual_detail.py` and `scripts/visual_detail/report_visual_detail.py` with the same interpreter. Preview the production build at `/?view=bgc-high-street&mode=inspect&detail=1`. For benchmark URLs add `debug=1&benchmark=1&quality=LOW`; for scripted walking use `mode=walk&benchmark_walk=1`.
