# Modeling guidelines

- Work in local metres. Preserve the package anchor and let the Blender glTF exporter perform Z-up to Y-up conversion.
- Model macro geometry before detail: footprint, height envelope, major volumes, silhouette, then supported facade regions.
- Keep observations separate from chosen parameters. Prefer editable ratios for uncertain features and link components to observation IDs.
- Do not infer precise portals, mullion spacing, storey mapping, service openings, or roof plant from partial evidence. Weak evidence requires lower geometric specificity.
- Use stable component IDs and deterministic names; production validation rejects defaults such as `Cube.001`.
- Keep authoring geometry semantically separated. Apply measured runtime optimization during export/integration and preserve source component IDs in merged metadata.
- Reuse shared materials only where visual function matches. Detect materially identical duplicates; never merge based on similar names alone.
- Prefer Python orchestration. Adopt Geometry Nodes only after a repeated pattern proves clearer reuse and reliable export.
- Use GPU instancing only for many identical meshes. Five nearby Central Square columns are simpler as one runtime batch.
- Validate silhouette, bounds, height, materials, metadata, triangle count, runtime meshes/draw calls, GLB bytes, and fixed QA renders.
- Keep unknown details omitted or visibly coarse. Blender is derived; canonical evidence remains under `data/`.

## Arbitrary polygon facades

Use the verified geographic polygon directly for irregular LOD1 massing. `PolygonEdgeFrame` derives edge start/end, length, angle, winding-aware outward normal, normalized u/v coordinates, vertical range, and depth. Keep edge regions separate in authoring; merge only explicit same-material groups for runtime. Validate winding, degenerate edges, tessellation, bounds, and re-imported GLB orientation. Never introduce irregular vertices from photographs alone.
