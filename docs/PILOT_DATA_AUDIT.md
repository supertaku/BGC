# Pilot data audit

Snapshot: `data/raw/osm/pilot-2026-09-10T134635Z.json`  
SHA-256: `09dc9d5aea72e11ad8d84d1c8d2e88132c0a5556e7a2f601824a0a7a74d4adcd`

## Measured coverage

| Metric | Count |
| --- | ---: |
| Building outlines | 31 |
| Building parts | 8 |
| Named building/part records | 27 |
| Records with explicit OSM height | 17 |
| Records with `building:levels` | 21 |
| Height from levels heuristic | 4 |
| Records with neither source height nor levels | 18 |
| Procedural height fallback | 18 |
| Roads | 88 |
| Pedestrian/path features | 269 |
| Open-space areas | 21 |
| POIs | 383 |

Height breakdown by feature kind: outlines contain 10 explicit geographic heights, 3 levels estimates, and 18 procedural fallbacks; parts contain 7 explicit heights and 1 levels estimate.

## Geometry and consistency checks

- Missing geometry/nodes in emitted features: **0**.
- Invalid emitted polygons after Shapely precision/validity processing: **0**.
- Duplicate canonical IDs: **0**.
- Rejected or repaired polygons: **0** for this snapshot.
- Suspicious explicit heights above 150 m: **4** (150.8–172.0 m). These are retained as OSM observations, not independently measured facts.
- Outline overlap greater than 1 m²: **2 pairs**. `osm:way:1071370327` overlaps Mariano K. Tan Center by about 1,197.4 m²; the B:5 outline overlaps the separately mapped Bench retail building by about 260.5 m². They may represent building/part or temporal mapping relationships. They are not silently rewritten.
- Building parts naturally overlap parent/outline areas; those overlaps are expected and preserved.

Road/path widths without an explicit `width` are estimated by documented class/lanes defaults. Buffered surfaces are derived, millimetre-snapped, validity-preserving unions for web-efficient Blender meshes; source centerlines remain in the canonical per-feature GeoJSON.

Machine-readable audit: `data/processed/pilot-data-audit.json`.
