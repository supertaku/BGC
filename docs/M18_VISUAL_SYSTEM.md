# M18 — Shared visual system prototype

Status: **PROTOTYPE, NOT GATED.** M17 has not passed, so M18 cannot be accepted. Earlier implementation work left an inspectable runtime prototype; this document does not claim finished city polish.

`web/components/runtime/visualSystem.ts` defines 11 shared MeshStandardMaterial families for glass, concrete, stone, metal, asphalt, sidewalk, grass and soil. Tile and landmark meshes are mapped by source material name, preserving multi-material arrays. The mapping is a coarse harmonization rule; it is not a source-verified material survey. No reusable bitmap textures, environment map, or KTX2 pipeline were added. This keeps texture transfer at zero for these changes, but glass reflections have not been evaluated.

`VisualEnvironment.tsx` adds a restrained sky/background, distance fog, hemisphere fill and one directional sun. FULL quality has a camera-local 1,024² shadow map, limited to a 360 m square; it is **opt-in and unbenchmarked**. LOW is the default and disables shadows. The existing OFF fallback remains. `EnvironmentManager.tsx` retains mapped object positions and instancing, and deterministically assigns three simple tree forms by ID. These are procedural tree variants, not botanical observations. The 452 source-grounded environment instances remain governed by active tiles; actual active instance and draw-call counts require browser capture.

No detailed crossings, lane paint, unique facade textures or surveyed road rules were invented. Runtime tile streaming and LOD switching were not replaced. Ground/road hierarchy is driven by broad material family assignment, but High Street pedestrian readability and whole-scene coherence have **not** passed visual walking QA.

The correct next gate is M17 visual signoff, followed by controlled M18 screenshots and identical M15/M18 foreground scenarios. Keep FULL shadows disabled by default until their measured cost is acceptable.
