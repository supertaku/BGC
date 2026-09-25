# M18A acceptance

**Decision: PASS for LOW; FULL rejected.** The default remains LOW with shadows off. LEGACY is available for A/B review. FULL's local shadows are available only with the explicit diagnostic benchmark URL and are disabled in the normal selector.

[Matched foreground captures](../data/reports/m18-foreground-captures.json) cover AERIAL, HIGH_STREET_INSPECT, HIGH_STREET_WALK, TOUR, and SOUTH_STREET in each quality mode. [Assessment](../data/reports/m18-performance.json) is reproducible with `python scripts/validation/assess_m18.py`.

| Scenario | LEGACY median | LOW median | LOW p1 vs LEGACY | LOW calls vs LEGACY |
| --- | ---: | ---: | ---: | ---: |
| AERIAL | 163.93 | 163.93 | +3.5% | +4.2% |
| HIGH_STREET_INSPECT | 163.93 | 163.93 | +11.4% | +11.1% |
| HIGH_STREET_WALK | 163.93 | 163.93 | -6.3% | +13.3% |
| TOUR | 163.93 | 163.93 | +32.4% | +7.8% |
| SOUTH_STREET | 163.93 | 163.93 | 0% | +18.2% |

The South Street draw-call increase is six calls across three instanced environment groups on a 33-call LEGACY base, below the 25% failure threshold and explained by added mapped environment. Transfers and active LOD1 counts match within each scenario. The 165 Hz cap limits interpretation of equal medians. Warm-cache Resource Timing transfer values are not cold-network costs. FULL walking p1 was 100 FPS versus LOW 126.58 FPS (-21%); High Street inspect and tour also fell more than 15%, so FULL is rejected.

Visual inspection passed for LOW's High Street and South Street views, tree materials, path/road hierarchy, search, tour, generic LOD2, and streaming. Scripted walking used the production collision/tile path; pointer-lock manual WASD was unavailable in the in-app browser and remains an explicit QA limitation. The seven published LOD1 assets and 94-tile manifest are preserved; no failed M17 draft is published.

With M16R PASS and PSE explicitly deferred after its bounded attempt, the v1 visual-fidelity release gate is **PASS_WITH_DOCUMENTED_LANDMARK_DEFERMENT**. M19 may begin after the final engineering regression checks recorded in this task. The largest visual weakness remains the PSE's unresolved pointed upper silhouette and body/frontpiece relationship.
