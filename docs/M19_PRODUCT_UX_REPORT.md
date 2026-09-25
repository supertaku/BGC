# M19 product experience report

Status: **PARTIAL** after M19C closure review. The public shell and deterministic validation pass, but desktop pointer-lock movement, a valid matched foreground performance guard, and 200% zoom remain unverified.

## Baseline and scope

- Starting branch: `main`; starting HEAD: `765473d55b7062af52c0d26e5e601e7f90ef5a5f`; starting working tree: clean.
- Node `v22.20.0`; npm `11.18.0`.
- No baseline discrepancy was found. The M18 assessor did contain a hard-coded FULL rejection requirement; it now derives LOW and FULL results from the capture thresholds. Existing measurements still yield LOW PASS and FULL REJECTED.
- The renderer, tile geometry, manifest transport, LOD boundaries, and spatial radii remain unchanged. A small navigation cleanup releases pointer lock and clears movement state when a mode ends.

## Product behavior

- BGC 3D uses full-viewport Canvas with a compact header and one contextual panel. Explore, Walk, Tour, Search, Help, and About are public. Tile, quality, metrics, and saved debug viewpoints appear only with `?debug=1`.
- Search ranks exact canonical names, exact aliases, canonical prefixes, alias prefixes, then canonical and alias substrings. It searches the 263 named entities in `bgc-interactive.json`. Duplicate names receive deterministic numbered URL slugs. The project-owned entity ID remains unchanged in source data.
- Search, Canvas selection, tour stops, and deep links converge on the same selected-place state. Public place details translate height provenance into plain language and omit IDs and LOD terms.
- Semantic links support `place`, `mode=walk`, and `tour=bgc-landmarks`; debug query parameters remain available. Browser Back/Forward restores place and tour. Share uses Web Share when available and Clipboard as fallback.
- The seven existing detailed assets form the tour. The UI does not invent landmark history or architectural descriptions.
- About explains mapped footprints, approximate background heights and generic objects, the estimated boundary, and the limits of survey use. The source snapshot is read from the manifest.
- A project-generated icon and Open Graph image are produced by `scripts/product/generate_brand_assets.py`.
- Social image URLs use `NEXT_PUBLIC_SITE_URL` when configured; local builds default to `http://localhost:3000`. A production origin must be set during deployment.

## Verification and remaining work

- Production build: PASS. Lint: PASS. Python repository tests: 55 PASS using the repository virtual environment's geospatial dependencies. Product-state validation: PASS. The two added assessor tests cover future FULL pass and LOW failure captures.
- Browser: Chrome rendered the city and place link, completed all seven tour stops, restored Back/Forward, and showed a safe invalid-place notice. A 726 px in-app viewport showed the bottom navigation and sheet layout.
- Browser automation's pointer-lock click produced `WrongDocumentError`; WASD, sprint, collision, and Esc release are **NOT_TESTED_IN_AUTOMATION**. Walk preparation and mode change were observed.
- A backgrounded Chrome benchmark returned about 1 FPS for High Street Explore, against M18 foreground LOW median 163.93 FPS. Those environments are not comparable. Matched High Street Explore, High Street Walk, and Tour performance must be captured in a foreground session before M19 can be signed off.
- This milestone does not begin M20.

## M19C closure review (2026-09-25)

Reviewed `main` at `3eb5c407420a74c104ba00df713d7b2274effa12` from a clean working tree. The original M19 starting SHA was `765473d55b7062af52c0d26e5e601e7f90ef5a5f`; machine reports use `base_sha` for that starting point and `reviewed_head_sha` for the commit audited here. Closure edits and reports were generated from an uncommitted worktree, so neither field claims to be the eventual release commit.

The URL restore path now applies one precedence rule: explicit debug navigation under `debug=1`, valid public tour, public place/Walk, benchmark navigation compatibility, then Explore. Debug tile and quality settings are restored with the same state. Search, Help, About, and Search-origin Place restore focus to the appropriate trigger. Search renders status text outside the listbox and keeps the active option valid. Touch devices receive an honest Walk availability message. About presents the geographic snapshot as a date.

Production build, lint, product-state verification, metadata verification, instancing verification, and 55 scoped Python tests pass. Chrome exercised public Search and Tour, place selection, Back restoration, debug precedence, and structural layouts at 390×844, 360×800, and 844×390. The Chrome pointer-lock click did not acquire lock, so movement and collision are not signed off. A Chrome Inspect benchmark produced a 1 FPS p1 sample despite 60 calls and 56,572 triangles; it is rejected as a throttled or interrupted run and does not establish a performance regression. Chrome 154/DPR 1.0 also differed from the M18 Chromium 153/DPR 1.25 reference. 200% zoom and soft-keyboard behavior were not reproduced. M19 remains PARTIAL, and Ready for M20 remains NO.

Duplicate-name slug numbering is deterministic but could shift after a future source-data refresh. M22 deployment must set `NEXT_PUBLIC_SITE_URL`; the localhost fallback remains appropriate before deployment.
