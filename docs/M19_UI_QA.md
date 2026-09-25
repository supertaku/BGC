# M19 UI QA

| Scenario | Result | Evidence |
| --- | --- | --- |
| Root and first-use entry | PASS | Chrome and in-app browser showed BGC 3D entry and public controls. |
| Named search, keyboard Enter | PASS | `central square` selected Central Square and produced `?place=central-square`. |
| Alias, prefix, substring, collisions | PASS | `npm run verify:product` checked alias SNR, prefix/substring, 263 unique readable links. |
| No-result wording | PASS | Chrome showed “No matching named place in the current BGC dataset.” |
| Valid place link and reload | PASS | Chrome loaded `?place=central-square` with focused scene and details. |
| Place plus Walk | PASS for preparation | Chrome loaded `?place=central-square&mode=walk` with details and pointer-lock instruction. |
| Invalid place | PASS | Safe fallback and temporary notice; viewer continued rendering. |
| Tour start, Next, Back/Forward | PASS | UI advanced from stop 1 to stop 7; browser history restored tour and place states. |
| Tour interruption | PASS | Chrome Search action exited Tour and opened Search; switching modes clears tour selection. |
| Walk pointer lock and movement | NOT_TESTED_IN_AUTOMATION | Controlled Chrome click raised pointer-lock `WrongDocumentError`. |
| Desktop visual layout | PASS | Chrome viewport showed full-bleed city with compact header and contextual place panel. |
| Narrow layout | PARTIAL | 726 px in-app viewport showed bottom modes and bottom sheet. Phone-width layout not exercised. |
| OSM attribution | PASS | Visible in both inspected layouts. |
| Debug separation | PASS | Tile/quality selectors and metrics absent normally; present with `?debug=1`. |
| Public bundle audit | PASS | No filenames matching research, comparison, draft PSE, or unpublished artifacts under `web/public`. |
| LOW visual system | PASS by code review | LOW remains the default; Canvas quality settings unchanged. |
| Matched performance | NOT_TESTED | Backgrounded browser benchmark cannot be compared with M18 foreground captures. |

Production build, lint, product-state validation, and 55 repository Python tests passed. The broad unscoped `pytest` invocation collected Blender scripts outside Blender and failed on missing `bpy`; the scoped repository test suite passed using the existing `.venv` geospatial packages.
