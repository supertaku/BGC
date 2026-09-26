# M23R–M24 handoff

Phase: **READY_FOR_USER_VALIDATION**. Milestone: Visual Fidelity Completion, Explore Controls & Graphics Settings.
Engineering and final benchmarks: PASS. Automated implementation/verification overall: **PARTIAL**, because the exhaustive live distance sweep and physical held-right input sequence are not fully verified. M23R and M24 are ready for user validation, not declared visually approved.

## Repository

Branch: main. Starting HEAD: `380ed7ccd2d3cfdfe2e51a2787b6bfaaae37416b`. Final HEAD: `380ed7ccd2d3cfdfe2e51a2787b6bfaaae37416b`. Working tree: DIRTY; changes are intentionally uncommitted.

## Facades and building identity

Vertical-facade audit: PASS, exact duplicate surfaces 0, coplanar violations 0, near-coplanar warnings 0; 1,196 opposing construction joins classified intentional. Opaque M23 facade materials use FrontSide (0 double-sided opaque facade materials). Roof/ground overlaps are outside this audit. Reversed depth ENABLED on the measured GPU. Explore near/far 0.4/8000m; Walk near 0.08m.

Canonical buildings 6,982; facade designed 6,982; uncovered/plain without a design 0. All 6,982 generic designs are procedural, across 18 families. This does not label them photographic reconstructions. One coincident OSM relation shares existing geometry. Evidence-informed architectural packages: 31 M23 landmarks, with estimated details explicitly labelled; seven pre-existing approved assets also follow persistent owner-tile visibility.

All 31 landmarks reviewed in six fixed rendered views (186 images). An exhaustive live near/250m/500m/1km visual sweep has NOT been completed: identity lost at distance is therefore not asserted as a measured zero. Identity visibility is tied to owner tiles; microdetail culling is implemented and configuration-tested, with visual acceptance pending.

## High Street

Hero ground coverage 100.00% of 39,330.19 m²; unknown/uncovered 0m²; holes above 4m²: 0. Paving, landscape, furniture, stairs/ramps and water: implemented; visual acceptance PARTIAL/AWAITING_USER_TEST. Connecting paving added 7,775.48m². Ground coverage is an exact partition of the authored envelope, not proof of photographic equivalence or every rendered overlap.

Shangri-La has three vertically stacked glazed bridges, raised arrival court, fountain and ramped passage. The final arrival circle is collision-checked against tall building volumes. Bridge arrangement is source-backed; dimensions and placement are estimated.

## Roads

Mapped roads analyzed: 1824; with numeric lane counts: 991. Marked-road count is not separately deduplicated in the retained report. Feature counts: 6,404 lane-divider pieces, 427 turn-arrow pieces, 1,582 road-edge pieces, 20 zebra stripe features, four stop bars, 248 painted bike-lane features, 942 bike-symbol components, 102 bike bollards, 88 traffic signals, 622 curb features and 31 bus-stop features. These are generated feature counts, not independently verified physical object counts. Source lane, turn, cycleway and one-way tags constrain generation; exact fixture spacing is inferred.

## Signage and art

41 anchors. Sign types: `{"BUILDING_NAME": 32, "PARK_SIGN": 8, "PUBLIC_REALM_BRAND": 1}`. Graphic logos: 2 official assets; photograph-backed brand placements: 2; text-only anchors: 39. Unverified physical placements: 39. Directory-only tenants are not placed on exterior facades. Temporary UNIQLO installation continued presence is unverified. Building-name/category counts come from the sign types above, not inferred corporate occupancy.

Official art records: 19; represented by neutral nearby-location markers: 19; reproduced artwork geometry: 0; licensed artwork textures: 0; deferred directory records: 0. Exact artwork positions remain estimated. Neutral markers are placeholders, not reproductions.

## Explore, Help and Graphics

Right-drag fixed-position look and right-held WASD: implemented and logic-tested PASS; physical held-input sequence remains AWAITING_USER_TEST. Left pan and scroll zoom: browser PASS. Text-input and boundary/ground safety: automated PASS, manual feel pending. Search transition interruption: browser PASS (one cancellation, no restart). Help's four exact Explore instructions: browser PASS.

Performance/Balanced/Quality configuration: PASS. Preference persistence and URL priority: automated PASS; browser selection/URL update, camera preservation, dialog focus trap, Escape and focus restoration: PASS. Canvas is not remounted when settings change.

## Runtime and performance

Full seven-stop Tour: seven completed transitions. Zero-visible events: 0; repeated tile requests: 0; LOD handoff gaps: 0; runtime errors: 0. Final benchmark console warnings/errors: 0.

| Profile | Valid runs | Mean FPS range | 1% low FPS range |
|---|---:|---:|---:|
| Performance | 5 | 165.57–168.14 | 97.09–144.93 |
| Balanced | 5 | 165.47–167.47 | 108.70–147.06 |
| Quality | 5 | 143.49–167.26 | 56.50–112.36 |

15/15 final runs valid, zero invalid/throttled final runs. Production build, foreground browser, 1000×760 CSS viewport, five-second warmup plus fifteen-second measurement. Quality Tour: 143.49 mean / 56.50 1% low FPS. All Walk routes exceed 100m cumulative travel. The earlier smoke test is excluded. Counts are end-of-sample, not peak allocation; results apply to this machine and viewport. Sealed runtime/assets fingerprint and production build ID match. A formatting-only spatial.ts change was restored to its exact sealed bytes before final validation; production assets/build did not change.

## Engineering and reproducibility

Build PASS; lint PASS; product PASS; Python 76 PASS; metadata PASS; M24 controls/configuration PASS; street controls PASS; public realm PASS; M23 ground/cache checks PASS. Full generation twice PASS (317 files); final targeted Shangri and street regeneration twice PASS, with separate retained reports. No new milestone, commit or push was performed.

## Manual validation

Facade flicker, distance fidelity, generic-building improvement, High Street environment, road realism, logo/sign accuracy, Explore camera feel and graphics visual difference: **AWAITING_USER_TEST**.

Preview: http://localhost:3002/?view=m23-high_street&graphics=balanced
Detailed evidence is in `data/reports/m23r-*.json`, `data/reports/m24-navigation-graphics.json`, `data/reports/m23r-browser`, and the seven required milestone documents. Reference provenance remains in `data/visual_reference/m23r`.
