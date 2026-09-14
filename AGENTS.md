# Agent operating instructions

Blender 5.2 is installed locally. It may not be on `PATH`; use `scripts/setup/find_blender.ps1` to resolve its executable. Control Blender primarily through background CLI execution and `bpy`. Use the GUI only for inspection or work that genuinely benefits from direct visual manipulation. Avoid repetitive GUI operations.

Turn deterministic, repeated work into reusable scripts. Make scripts idempotent where practical, fail clearly, and avoid regenerating successful assets without a validation reason. Preserve reproducibility: paths should be repository-relative, inputs and provenance should be retained, and generated outputs must be derivable from committed source data and scripts.

Never invent real-world architectural details and present them as verified. Label observations and fields as one of: verified geographic data, verified photographic evidence, inferred information, estimated information, or procedurally generated filler. Retain source provenance when real data is introduced.

Design geometry, materials, textures, and exports for web delivery. Performance is a first-class constraint: track draw calls, material count, geometry density, texture memory, asset size, instancing, LOD, and spatial loading implications.

Before significant architectural changes, read:

- `AGENTS.md`
- `docs/ARCHITECTURE.md`
- `docs/DECISIONS.md`
