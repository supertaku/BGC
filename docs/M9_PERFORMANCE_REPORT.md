# M9 performance report

## Asset cost

| Metric | W Global LOD1 | Combined pilot | M8 pilot baseline |
| --- | ---: | ---: | ---: |
| GLB bytes | 73,904 | 1,033,348 | 962,916 |
| Triangles | 1,032 | 21,096 | 20,076 |
| Vertices | 2,064 | 34,461 | not recorded |
| Runtime meshes / calls | 12 | 71 | 60 |
| Materials | 5 | 17 | 16 |

The 7.3% pilot byte growth and 5.1% triangle growth are modest. Draw calls rise 18.3%, inside the M8 warning band but below failure. The first unoptimized integration reached 91 calls; explicit runtime batches reduced it to 71 while preserving 86 semantic authoring meshes and 1,032 triangles.

## Browser benchmark

Methodology was unchanged: Next.js production build; 759 × 742 CSS pixels; DPR 1; 5,000 ms warmup; 15,000 ms requestAnimationFrame sampling; fixed saved cameras. Chromium-family in-app browser, same host class as M8. No console warning/error was observed during validation.

| Scene | Mean FPS | Median FPS | P1 low | Calls | Visible triangles | Load ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| PILOT_OVERVIEW | 165.20 | 163.93 | 151.52 | 71 | 21,096 | 407 |
| CENTRAL_SQUARE_NEAR | 165.21 | 163.93 | 151.52 | 40 | 19,536 | 381 |
| CENTRAL_SQUARE_STREET | 165.14 | 163.93 | 153.85 | 31 | 19,344 | 385 |
| W_GLOBAL_NEAR | 165.35 | 163.93 | 153.85 | 24 | 20,028 | 383 |
| W_GLOBAL_STREET | 165.22 | 163.93 | 151.52 | 33 | 20,292 | 394 |

There is no material matched-environment FPS regression. Accumulating draw calls and nodes remains more informative than FPS at this pilot size.
