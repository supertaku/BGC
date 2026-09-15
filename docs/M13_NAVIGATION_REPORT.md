# M13 Navigation Report

Status: **PARTIAL**. Inspect, selection, search, and the seven-stop tour passed browser QA. Walk is implemented, but synthetic automation could not validate a real pointer-lock session.

## Navigation and interaction

Navigation has explicit `INSPECT`, `WALK`, and `TOUR` states. Inspect owns OrbitControls. Walk owns Drei PointerLockControls, documents WASD/arrow keys, Shift sprint, and ESC unlock, and moves at `speed * delta`. Default speed is 7 m/s, sprint is 18 m/s, and eye height is 1.7 m. Leaving Walk restores the saved inspect camera.

Walk collision uses only footprints from active-tile sidecars. Candidate positions are tested against the project working polygon and nearby building footprints with a 0.65 m margin. The polygon is clearly retained as an estimated working boundary, not presented as a physical wall. No physics engine or all-building per-frame raycast was added.

Selection separates interaction geometry from merged render geometry: a screen ray meets the ground plane, then the smallest containing active-tile footprint resolves the entity. Search uses a 263-record static name/alias index and focuses the camera. The detail panel shows existing ID, name, height, height evidence, building type, and LOD availability.

The guided tour uses the seven existing detailed landmarks. Camera transitions run through refs and `useFrame` easing; reduced-motion preferences collapse the duration, and Exit Tour restores manual inspection.

## Browser QA

- Central Square was found, selected, and focused from search: PASS
- Selection metadata and LOD status displayed: PASS
- Tour opened and advanced from stop 1 to stop 2: PASS
- Walk UI and first-use controls activated: PASS
- Real pointer lock and movement: PARTIAL. Automation returned `WrongDocumentError`; a foreground manual mouse-lock pass is still required.

Machine-readable evidence is in `data/reports/m13-navigation.json`.
