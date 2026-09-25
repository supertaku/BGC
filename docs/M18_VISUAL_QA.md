# M18A foreground visual QA

Status: **LOW PASS with manual input limitation; FULL REJECTED**. The production Next.js build was inspected in the foreground Codex Chromium browser at 726 × 742 CSS pixels on Intel Iris Xe. Five matched scenarios were captured in LEGACY, LOW, and FULL with 5 s warmup and 15 s frame sampling. [Raw captures](../data/reports/m18-foreground-captures.json) retain FPS, Resource Timing bytes, draw calls, triangles, geometries, textures, active tiles, active LOD1, and environment groups.

High Street and South Street viewpoints were corrected to look along mapped paths/roads. LOW showed readable road/path contrast, daylight materials, fog/sky, and brown-trunk/green-crown trees. Central Square and W Global search/focus, seven-stop tour, generic South Street LOD2, and tile streaming were inspected. The seven original LOD1 assets remain in the manifest, and no PSE draft appeared.

The HIGH_STREET_WALK benchmark moved approximately 283 m using the normal collision and tile-loading code; 26 tiles were active at the endpoint versus 22 on initial High Street. The in-app browser blocked pointer lock, so manual WASD and free mouse look were **not independently signed off**. This is a browser input limitation, recorded for later device QA; it does not alter the matched visual-system result.

All five LOW medians equal the LEGACY 163.93 FPS display cap. LOW walking p1 was 126.58 versus LEGACY 135.14 FPS, a 6.3% decrease, within the 15% review threshold. Resource Timing decoded bytes and active LOD1 matched across modes in each scenario. Warm-cache transferSize is not a cold-network benchmark. LEGACY renders at DPR 1, LOW at current capped DPR. These results establish a matched product-mode comparison, not spare GPU headroom.

FULL p1 falls more than 15% below LOW in High Street inspect, walking, and tour. Shadow popping was not signed off, so FULL is rejected for v1 and disabled in the normal selector. See [acceptance report](M18_ACCEPTANCE_REPORT.md) and [performance report](../data/reports/m18-performance.json).
