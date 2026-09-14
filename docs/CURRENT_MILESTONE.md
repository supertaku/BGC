# Current milestone

## M11 — Whole-BGC Low-Fidelity Skeleton

Status: **PASS** as of 2026-09-15.

The estimated 4.724 km² project boundary is now represented by 94 deterministic 250 m tiles containing 6,982 canonical LOD2 buildings, 1,824 roads, 1,226 paths, and 206 open spaces. All tile exports passed. The browser loads the full city plus seven separate LOD1 landmarks at 15.58 MB initial transfer and measured 156.69 mean aerial FPS on the current machine.

Height evidence remains the principal limitation: 94.78% of features use deterministic procedural fallback heights. See `docs/M11_WHOLE_BGC_REPORT.md` and the structured anomaly queue in `exports/bgc/manifest.json`.

## Explicit non-goals

- no per-building facade research or new LOD1 reconstruction;
- no LOD0, interiors, traffic, NPCs, final UI, or full spatial streaming;
- no unsupported photorealism or arbitrary landmark polishing;
- no Astra use.

## Recommended next milestone

**M12 — Targeted height-evidence cleanup and selective LOD refinement**, using Terra for deterministic audits and Sol only for difficult building-part semantics.
