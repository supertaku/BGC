# Provisional reconstruction performance budget

This bootstrap has principles, not production promises. Numerical targets remain provisional until representative city tiles are benchmarked on target devices.

- Track triangles, vertices, materials, textures, draw calls, and decoded GPU memory per spatial tile and for each representative view.
- Prefer instancing for vegetation, street furniture, and repeated facade elements; merge static geometry only when it does not damage culling or reuse.
- Establish LOD from measured screen-space contribution. Keep distant geometry silhouette-focused and avoid details smaller than their projected pixels.
- Partition the city spatially. Load the near field first, lazy-load surrounding tiles, and unload assets outside a defined working set.
- Keep material variants deliberate. Favor shared materials and texture atlases where they reduce draw calls without creating impractical updates.
- Select texture resolution from visible texel density, not source-photo size. Plan for mipmaps and KTX2/Basis compression after baseline compatibility is proven.
- Measure GLB transfer size and parse/decode time separately. Split assets when a monolith harms initial load or memory.
- Desktop and mobile require separate measurements. Cap device pixel ratio and shadow cost on constrained devices; provide lower LOD and texture variants when evidence supports them.
- Treat shadows, transparency, post-processing, and real-time lights as explicit costs.

## LOD1 per-building anomaly bands

These are review signals derived from the first 356-triangle/18-runtime-mesh asset, not architectural limits.

| Metric | GREEN | WARNING | REVIEW |
| --- | ---: | ---: | ---: |
| Triangles | ≤1,500 | 1,501–5,000 | >5,000 |
| Runtime meshes / approximate draw calls | ≤20 | 21–35 | >35 |
| Materials | ≤8 | 9–12 | >12 |
| GLB bytes | ≤250 KB | 250 KB–1 MB | >1 MB |

A distinctive building may exceed a band with a documented reason. Prioritize disproportionate object/material/draw-call growth before reducing already-cheap silhouette geometry.

## LOD and optimization

- LOD0: future evidence-rich landmark detail; not generated in M8.
- LOD1: recognizable medium fidelity preserving footprint, height, massing, major facade regions, and supported entrances/roof forms.
- LOD2: basic mass plus coarse evidence-class material treatment.
- LOD3: optional distant proxy introduced only after measured distant-scene cost.

Future transitions require distance thresholds, hysteresis, fallback assets, stable bounds, and non-blocking loading. Streaming is outside M8.

Merge meshes when measured draw-call pressure rises and common material/role/LOD/culling boundaries make the merge safe. Use GPU instancing for many identical meshes. Use mesh compression only when aggregate transfer/parse cost becomes material; 44 KB does not justify it. Use KTX2 after measured texture pressure; Central Square has zero textures. Add LOD3 only after measuring distant-building cost.

## Reproducible browser benchmark

Benchmark a production build at a recorded CSS viewport and device pixel ratio. Use fixed `overview`, `central-square`, and `central-square-street` views. Warm up 5 seconds, measure frame intervals for 15 seconds, and report mean, median, 1st-percentile-low, minimum, and maximum FPS plus load duration, console errors, asset bytes, `renderer.info` calls/triangles/geometries/textures, logical CPU count, RAM when exposed, GPU when exposed, browser/version, and backend. One instantaneous FPS sample is never primary evidence.

Browser errors or identity/metadata mismatch fail. More than 25% unexplained draw-call/material/GLB growth fails; 10–25% warns. More than 15% matched-environment median-FPS loss warns and more than 25% fails.
