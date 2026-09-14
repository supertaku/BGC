# M10 framework report

Framework status: **STABLE**. Schema 1.0 remained unchanged. Five targets use shared footprint extrusion, material families, evidence metadata, QA cameras, runtime merge/export, and GLB validation. `PolygonEdgeFrame` is the only new shared primitive; it maps normalized u/v regions onto any exterior polygon edge with winding-aware outward normals.

Wave A found one backwards-compatibility defect: the generic builder assumed every GeoJSON feature had a top-level `id`, while the legacy fixture stores it in `properties.id`. The fallback was added and the fixture then passed. Central Square visual/semantic regression, W Global rebuild, metadata transport, and all 34 pre-M10 tests passed. With five M10 tests, the final suite is 39 tests.

There are five target configurations and zero target-specific Python builders. The 232 semantic authoring meshes become 12 standalone runtime meshes. No GPU-instancing extension was justified: merging same-material edge bands is simpler at this scale.
