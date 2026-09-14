# M7 performance report

## Asset delta

| Metric | Before M7 | After M7 | Delta |
| --- | ---: | ---: | ---: |
| Pilot GLB size | 919,392 B | 950,388 B | +30,996 B (+3.37%) |
| Imported triangles | 19,896 | 20,076 | +180 (+0.90%) |
| Imported meshes | 46 | 67 | +21 |
| Materials | 10 | 16 | +6 |
| Draw-call approximation | 46 | 67 | +21 |
| Textures | 0 | 0 | 0 |

The standalone Central Square asset is 51,204 bytes with 356 triangles, 25 meshes, 6 materials, and no textures. Replacing four original Central Square extrusion meshes with 25 LOD1 meshes explains the net +21 mesh/draw-call change.

## Browser spot check

The after-M7 production build was checked in the Codex in-app Chromium browser at the same 759 × 742 CSS-pixel viewport recorded for M6.

| View | Visible triangles | Calls | Warm FPS spot sample | Load ready |
| --- | ---: | ---: | ---: | ---: |
| Overview | 20,076 | 67 | 165 FPS | 385 ms |
| Central Square / 30th Street | 19,536 | 47 | 165 FPS | same loaded session |

The browser console contained zero warning/error entries. The M6 baseline warm samples were 108–128 FPS overview and 117–124 FPS street level, but the before/after runs differ in server mode and machine/app state. The higher M7 spot samples must not be interpreted as a causal performance improvement. The defensible conclusion is that no regression appeared in this limited fixed-camera desktop check, while the asset cost remains small in triangles and transfer size. Mesh/draw-call growth is the main cost to watch when this pattern is repeated across more buildings.

## Status

Production build: PASS. Pilot load: PASS. Central Square viewpoint: PASS after correcting the Blender-to-Three.js camera-axis conversion. Console: PASS. Provisional desktop performance: PASS. Mobile and controlled 1% low benchmarking remain future work.

