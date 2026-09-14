# Central Square reconstruction package v2

This is the M6 handoff for `bgc_building_0014` (Central Square, Bonifacio High Street Central). It is self-contained when read with the repository `AGENTS.md` and modeling guidelines. Detailed Blender reconstruction has not started.

## Readiness

**RECONSTRUCTION_READY_WITH_GAPS** for a recognizable LOD1 / medium-fidelity first pass representing approximately 2025–2026 permanent architecture.

Use the existing OSM-derived local-metre geometry as horizontal control. The mapped footprint is 6118.37 m² with an oriented envelope of approximately 87.08 × 80.68 m and a mapped maximum height of 25.9 m. The height is explicit OSM geographic evidence, not an authoritative survey.

Target-local sides are:

- north: 30th Street;
- west: 5th Avenue;
- south: Bonifacio High Street / BHS Central pedestrian corridor;
- east: adjacent-building/service side.

The north facade and overall massing are well enough evidenced. West and south are partial. The east/service side, exact public-entry portals, basement access, and roof equipment remain unresolved. Follow `unknowns.json` and the `do_not_invent` rules in `reconstruction_spec.json`.

## Evidence and rights

`references.json` separates reusable Commons files from research-only official, article, and video sources. The 2015 Commons image is correctly classified as an **interior atrium** image, not a facade. No image file is bundled; metadata and source-native hashes are retained. Before redistributing any image or derivative, follow `rights.json` and assemble creator/title/source/license/change attribution.

## Modeling order

1. Load `geometry.geojson` in the existing EPSG:32651-derived local frame.
2. Build the component plan in `massing.json` without changing mapped dimensions.
3. Implement the north, west, and south facade structures from `facades.json`.
4. Use only the placeholder entrance guidance in `entrances.json`.
5. Apply the coarse families in `materials.json`; do not copy research-only imagery or campaign artwork.
6. Render the diagnostic views in `reconstruction_spec.json` and compare only against the linked references.
7. Keep the east facade and roof equipment deliberately low-detail until new evidence exists.

Regenerate this package with:

```powershell
.\.venv\Scripts\python.exe scripts\reconstruction\build_central_square_package.py
```

Validate it with:

```powershell
.\.venv\Scripts\python.exe scripts\reconstruction\validate_package.py data\reconstruction_packages\bgc_building_0014
```
