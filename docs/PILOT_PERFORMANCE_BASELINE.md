# Pilot performance baseline

Measured 2026-09-10 in the Codex in-app Chromium browser against the Next.js development server at a 759 × 742 CSS-pixel window. FPS is a one-second rolling counter; the warm samples below are five-second fixed-camera spot checks, not a production 1% low benchmark.

## Asset baseline

| Metric | Result |
| --- | ---: |
| GLB size | 919,392 bytes (0.88 MiB) |
| Imported meshes | 46 |
| Imported triangles | 19,896 |
| Materials | 10 |
| Draw-call approximation | 46 |
| Bounds | X −383.397…142.080 m; vertical −0.180…172.000 m; other horizontal −252.569…199.912 m |
| Textures | 0 |

## Browser spot checks

| View | Visible triangles | Calls | Warm FPS samples | GLB/manifest ready |
| --- | ---: | ---: | --- | ---: |
| Overview | 19,896 | 46 | 108, 123, 128, 127 FPS | 442 ms |
| High Street street level | 19,608 | 33 | 117, 121, 122, 124 FPS after tab cleanup | 805 ms |

The browser console had **0 warning/error entries** after both loads. The lower visible counts at street level are consistent with frustum culling. These results clear the provisional desktop pilot budgets with large margin, but they must not be generalized to mobile hardware or production-network transfer.

Memory is only partially observable here: renderer counters reported geometry/texture allocations to the page, but no calibrated process/GPU memory tooling was available. A later M10 benchmark should use a named physical device, production build, fixed 30-second route, 1% lows, transfer timing under a defined network profile, and a constrained/mobile viewport.
