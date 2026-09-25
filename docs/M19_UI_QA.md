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

## M19C closure QA (2026-09-25)

| Gate | Result | Evidence |
| --- | --- | --- |
| Public URL normalization | PASS | Product validation covers place, Walk, Tour and invalid links; Chrome exercised place, Walk prep and Tour. |
| Debug and benchmark Walk URLs | PASS for URL state | Product validation covers debug precedence and benchmark Walk navigation. |
| Back/Forward | PASS for exercised path | Chrome restored Tour after Search interruption and place selection. |
| Search no-results semantics | PASS | Chrome showed collapsed combobox, status, no listbox or active descendant; Arrow/Enter caused no selection. |
| Focus restoration | PASS for exercised exits | Chrome returned Place to Search and Help Escape to Help; About has a dedicated trigger ref. |
| 390×844 and 360×800 | PASS structural | Header/mode controls and attribution measured within viewport; no horizontal document overflow. |
| 844×390 | PASS structural | Close and attribution stayed in viewport; panel remained scrollable. |
| Soft keyboard | NOT_TESTED | Browser viewport override did not reproduce a phone soft keyboard. |
| 200% zoom | NOT_TESTED | Controlled Chrome did not produce a verified 200% zoom state. |
| Pointer-lock Walk | NOT_TESTED | Canvas click left `document.pointerLockElement` unset. |
| Reduced motion | NOT_TESTED in browser | Preference was not toggled in this session. |
| Share | NOT_TESTED | Native Share and Clipboard fallback were not exercised. |
| Foreground performance | NOT_VERIFIED | Inspect mean 160.29, median 163.93, p1 1 FPS; rejected for throttling/interruption and browser/DPR mismatch. Walk and Tour not captured. |
| Public bundle and metadata | PASS | No research/PSE/draft artifact filenames in `web/public`; built metadata and image/icon routes exist. |

M18 LOW references remain in `data/reports/m18-foreground-captures.json`. The invalid M19 Inspect observation is retained for provenance in `data/reports/m19-ui-validation.json`.
