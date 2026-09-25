# M19 accessibility review

Result: **PARTIAL**. This is an implementation review, not an accessibility certification.

## Implemented

- The header, mode navigation, Search, place details, Help, About, tour, and OSM attribution have accessible labels. Search is available without using the 3D Canvas.
- Search exposes a combobox and listbox. Arrow keys change the active option, Enter selects it, Escape closes the panel, and Tab retains normal browser focus movement. Search selection opens place details.
- Public buttons have visible focus outlines. Primary mode buttons are at least 42 px tall on desktop and 48 px in the narrow layout. Panels scroll within the available viewport height.
- Panels are mutually exclusive. Escape closes the current panel and returns focus to the Search or Help trigger. The interface avoids per-frame screen-reader announcements; the runtime notice uses a status region.
- `prefers-reduced-motion` shortens camera transitions in the existing navigation controller, and CSS removes long UI animations. Named-place search, details, and the seven tour stops provide non-Canvas access to the core content.

## Evidence and limits

- Chrome accessibility-tree inspection confirmed Search semantics, the no-result state, place details, tour controls, and attribution. Keyboard Enter selection was exercised. The seven tour stops were advanced through the UI.
- The 726 px narrow layout was visually inspected. A phone-sized viewport, 200% zoom, a dedicated screen reader, and a full keyboard-only pass were not completed.
- Help, About, Search, and Place are nonmodal panels rather than modal dialogs. Their focus order remains in document order; a formal focus-trap test is not applicable. Focus restoration after every exit path still needs manual verification.
- Pointer-lock movement could not be validated through browser automation because the controlled document rejected pointer lock.
