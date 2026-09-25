# M19 product experience report

Status: **PARTIAL**. The public product shell is implemented, while pointer-lock movement and a matched foreground performance comparison remain unverified in this automation environment.

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
