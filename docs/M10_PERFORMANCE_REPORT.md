# M10 performance report

The production Next.js build passes and the browser console has zero warnings/errors. Methodology matches M8/M9: 759×742 CSS viewport, Canvas DPR 1, 5 s warmup, 15 s requestAnimationFrame sampling, fixed cameras, same host/browser family. Windows reports a desktop devicePixelRatio of 1.25; the Three.js Canvas remains explicitly fixed to DPR 1.

Overview: 165.84 mean, 163.93 median, 153.85 p1 FPS; 76 calls, 23,796 rendered triangles, 76 geometries, 0 textures. The lowest new-building mean is C1 at 165.36 FPS; the lowest new-building p1 is 140.85 FPS at One Maridien/JY Campos. FPS remains secondary to the measured scene costs. Full per-camera data is in `data/reports/m10-browser-benchmark.json`.
