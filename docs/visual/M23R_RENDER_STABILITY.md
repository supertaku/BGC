# M23R render stability

The landmark shell compiler unions duplicate fronts, clips competing coplanar surfaces, removes identical internal joints, and keeps opaque materials FrontSide. It does not rely on global polygon offset. Structural glazing has physical separation from the mass.

Current audit: **PASS**, tolerance 0.02m. Counts: `{"INTENTIONAL_OVERLAY": 1196}`. Scope includes vertical triangles, box faces and landmark sign planes. Opposing construction joins are retained as intentional overlays. Ground and roof overlap are outside this vertical-facade audit.

Explore uses near 0.4m / far 8000m, Walk near 0.08m; reversed depth is requested and the actual GPU support is captured with each benchmark. Unsupported GPUs retain Three.js's normal depth path.

All 31 landmarks have six fixed camera renders. The eight contact sheets in `data/reports/m23r-review` were inspected. Live near/far flicker remains **AWAITING_USER_TEST**.
