# M18 — Visual and performance QA

Status: **NOT RUN as an acceptance suite.** The M17 prerequisite failed. The system has a compile/test check and static asset accounting, not a valid M15-to-M18 foreground benchmark.

The required matched scenarios remain AERIAL, HIGH_STREET_INSPECT, HIGH_STREET_WALK, TOUR and SOUTH_STREET. For each, capture initial and streamed bytes, draw calls, triangles, geometry and texture counts, mean/median/p1 FPS, camera position, viewport, GPU and quality preset. Repeat at LOW and FULL to isolate shadow cost. The prior [M11 Chrome benchmark](../data/reports/m11-browser-benchmark.json) used an older all-loaded runtime and only three scenarios; its 15,580,452 initial bytes and 167.9 mean High Street FPS are **not** a comparable M15 baseline. [M18 performance](../data/reports/m18-performance.json) therefore records null before/after values, not invented gains.

Visual walking QA still needs fixed views along High Street, Central Square, W Global, the tour route and generic LOD2 blocks. Review ground-to-building contact, sky/fog legibility, daylight material response, tree instancing/variation, LOD1-to-LOD2 contrast, and geographic placement. FULL must also demonstrate a bounded local shadow frustum without popping or unacceptable p1 loss.

Automated build/lint/tests can pass while these visual and performance gates remain incomplete.
