# M18A visual system acceptance

Status: **NOT GATED**. M18A starts after the final revised M17 batch is individually approved. The existing shared materials, VisualEnvironment, tree variants, mapped instancing, and LOW default are preserved.

There is no historical comparable M15 browser baseline. Do not infer one from the M11 report. When M17 passes, benchmark the same final runtime in controlled legacy/LOW/FULL modes across AERIAL, HIGH_STREET_INSPECT, HIGH_STREET_WALK, TOUR, and SOUTH_STREET in a foreground browser. Record mean/median/p1 FPS, initial and streamed bytes, draw calls, triangles, geometries, textures, active tiles, active LOD1, GPU, viewport, and DPR. Apply the existing >15% warning and >25% failure gates. Assess walking visual coherence, shadow popping and p1 stability before considering FULL; LOW remains default.

`data/reports/m18-performance.json` remains `NOT_GATED` with null comparable measurements. No M18 acceptance or production build claim is made here.

## Original M18 prototype assessment


Status: **NOT RUN as an acceptance suite.** The M17 prerequisite failed. The system has a compile/test check and static asset accounting, not a valid M15-to-M18 foreground benchmark.

The required matched scenarios remain AERIAL, HIGH_STREET_INSPECT, HIGH_STREET_WALK, TOUR and SOUTH_STREET. For each, capture initial and streamed bytes, draw calls, triangles, geometry and texture counts, mean/median/p1 FPS, camera position, viewport, GPU and quality preset. Repeat at LOW and FULL to isolate shadow cost. The prior [M11 Chrome benchmark](../data/reports/m11-browser-benchmark.json) used an older all-loaded runtime and only three scenarios; its 15,580,452 initial bytes and 167.9 mean High Street FPS are **not** a comparable M15 baseline. [M18 performance](../data/reports/m18-performance.json) therefore records null before/after values, not invented gains.

Visual walking QA still needs fixed views along High Street, Central Square, W Global, the tour route and generic LOD2 blocks. Review ground-to-building contact, sky/fog legibility, daylight material response, tree instancing/variation, LOD1-to-LOD2 contrast, and geographic placement. FULL must also demonstrate a bounded local shadow frustum without popping or unacceptable p1 loss.

Automated build/lint/tests can pass while these visual and performance gates remain incomplete.
