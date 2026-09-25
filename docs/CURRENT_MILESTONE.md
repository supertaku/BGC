# Current milestone

## M16–M18 — Visual Fidelity Expansion

Status: **PARTIAL** as of 2026-09-25. M16 ranked 6,982 candidates and selected ten priorities, but one remains NOT_READY due to a height conflict. M17 produced ten structurally valid draft LOD1 assets before that conflict was isolated; visual QA found major architectural discrepancies. All ten remain `PENDING_VISUAL_QA` and the published world still contains the original seven LOD1 assets. M18 shared materials/lighting/vegetation are a prototype only, with LOW quality default and no comparable foreground benchmark. See `docs/VISUAL_FIDELITY_REPORT.md`.

Next gate: **M17 reference-matched reconstruction and signoff**, starting with the wave-A landmarks. Do not publish drafts or claim M18 acceptance until that gate passes.

## Historical M11 — Whole-BGC Low-Fidelity Skeleton

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
