# Reconstruction pipeline

## Coordinate contract

```text
EPSG:4326 longitude/latitude
    -> EPSG:32651 WGS 84 / UTM zone 51N
    -> subtract fixed BGC origin
    -> local east/north/up metres
    -> Blender X/Y/Z metres
    -> Blender glTF exporter
    -> glTF / Three.js X/Y/Z (Y up)
```

The fixed origin is longitude `121.050972`, latitude `14.550806`, near the pilot center. Its location is a convenient engineering origin, not an official BGC datum. Horizontal coordinates use [EPSG:32651](https://epsg.org/crs_32651/WGS-84-UTM-zone-51N.html), whose area of use includes 120°E–126°E in the northern hemisphere and whose units are metres. `scripts/geography/geo_utils.py` uses pinned `pyproj` transformations with `always_xy=True`; `scripts/validation/test_coordinates.py` tests the central-meridian invariant, round trips, direction, three geodesic-versus-projected distances, and pilot area.

Altitude is separate. Ground is initially a local `z=0` plane. Absolute elevations and terrain must carry a vertical datum before use; otherwise they are `ESTIMATED` or `UNKNOWN`. Building height is relative to local ground. Blender uses Z-up; the exporter performs the glTF Y-up conversion. The viewer must not apply a compensating rotation.

## Current real-data experiment

```text
pilot-boundary.geojson
    -> fetch_osm.py (immutable raw snapshot + metadata + hashes)
    -> normalize_osm.py (Shapely validity/precision, relations, holes, parts, surfaces)
    -> generate_bgc_pilot.py (grounded diagnostic scene + five fixed cameras)
    -> .blend + five PNGs + GLB + re-import metrics + viewer manifest
```

Run the cached, repeatable experiment:

```powershell
./scripts/validation/run_pilot_experiment.ps1
```

Pass `-RefreshOsm` only when intentionally reviewing a new upstream snapshot. The default fetch is idempotent and reuses the latest boundary/query-matched cache. The current pilot processes the complete cached extract clipped to the canonical central-core boundary. It proves source → immutable cache → robust normalization → local coordinates → Blender → GLB re-import → manifest-driven Three.js without introducing facade claims.

Current limitations before visual refinement:

- Explicit OSM height tags are verified geographic attributes, not independently surveyed elevations.
- Estimated and procedural heights remain diagnostic and are color-coded in Blender.
- Road/path surfaces are derived from centerlines and explicit or class-based width assumptions.
- No facade, entrance, roof-detail, or material appearance is presented as verified photographic evidence.
- The next evidence milestone is reference acceptance/entity matching and coverage, not higher geometric detail.

## Procedural reconstruction responsibilities

| Concern | Preferred implementation | Reason |
| --- | --- | --- |
| Footprint cleanup/extrusion, floor bands, roof volumes, road/path surfaces, sidewalks, markings | Python/`bpy` driven by normalized records | Deterministic, batchable, easy to version and regenerate. |
| Repeating facade bays or parametric panels within a building | Python first; Geometry Nodes only after a repeated authoring pattern is proven | Avoid embedding essential logic in opaque node graphs too early. |
| Trees, shrubs, benches, lights, bollards, signs, bins, traffic lights | Reusable mesh prototypes and collection instances | Reduces mesh duplication and authoring cost. |
| Generic doors/windows/storefront modules | Shared modular meshes/material families; bake/merge per LOD when measurement supports it | Preserves reuse while allowing draw-call optimization. |
| Surface variation and distant facade detail | Shared materials, trim sheets/atlases, later KTX2 textures | Cheaper than unique geometry; resolution follows visible texel density. |
| Landmark silhouette corrections and evidence-specific entrances | Manual or scripted override layered above the generated base | Keeps verified exceptions without forking the whole pipeline. |

AI reasoning decides what evidence supports and which generator/override is appropriate. Deterministic scripts decide how repeated geometry is produced.

## Asset library

Use semantic names: `BGC_<category>_<family>_<variant>_vNN`, for example `BGC_tree_tropical_medium_v01`. Each asset metadata record includes category, dimensions in metres, pivot/orientation, material IDs, triangle count, LODs, license/provenance, generator version, and collision proxy status.

Keep global reusable source assets in small category `.blend` libraries (`vegetation.blend`, `street_furniture.blend`, `facade_modules.blend`) rather than a city master file. Export web-ready shared bundles only when runtime tests show that cross-tile reuse offsets extra requests. Repeated scene objects should be linked duplicates or collection instances.

## Blender scene architecture

Use generated per-tile `.blend` files plus separate source asset libraries and separate manual override files:

```text
normalized data + generator version
    -> generated tile scene (disposable)
asset libraries -------------------^
manual landmark override ----------^ (linked or merged by export job)
```

Do not create one enormous master `.blend`. Per-tile generation limits crash/regeneration scope, supports parallel batch export later, and aligns with web streaming. A lightweight QA assembly scene may link several adjacent tile collections for seam checks; it is not canonical source data.

## Spatial partitioning

Start with a **250 m square grid in EPSG:32651**, indexed from the fixed project origin. It aligns with metric operations, gives roughly four tiles across a one-kilometre corridor, and can be revised after benchmarks. Tile IDs encode signed integer east/north indices, not names tied to changing neighborhoods.

- Buildings belong to the tile containing their footprint centroid and are not split. Their bounds are registered so adjacent tiles can request them when visible.
- Roads, paths, and large open spaces are clipped per tile with a small deterministic seam overlap; source entity IDs remain shared.
- Landmark far-LOD assets live in a visibility registry and can load outside their owner tile.
- Collision/navigation data follows the same tile grid but is independently simplified.
- The tile manifest records bounds, asset URLs, hashes, LOD metrics, dependencies, and attribution source IDs.

Do not implement streaming until the pilot viewer has tile-shaped manifests and measured load/unload behavior.

## LOD contract

| LOD | Survives | Removed/simplified |
| --- | --- | --- |
| LOD0 | Evidence-backed silhouette, major setbacks, entrance/storefront cues, visible material groups | Sub-pixel hardware, unseen details, geometry represented well by textures. |
| LOD1 | Recognizable massing, principal facade rhythm, major roof shape, coarse materials | Small bays, recessed details, furniture attached to building. |
| LOD2 | Footprint-derived mass, major height changes, dominant color/material | Openings and most facade geometry. |
| LOD3 | Very cheap silhouette or cluster proxy, dominant tone | Individual facade structure and minor footprint articulation. |

Blender should generate LOD2/3 from source parameters, not by blindly decimating. Meshoptimizer can be tested for transfer/vertex-cache optimization and selective simplification after silhouette checks. Three.js chooses LOD using projected screen size with hysteresis; distance-only thresholds are a first approximation, not the final contract.

## Visual QA

Every Tier A/B building receives fixed, versioned cameras: north, south, east, west orthographic/elevation views; two street-level views tied to navigation routes; one three-quarter view; and one aerial/context view. Camera transforms, lens, crop, and target entity are data.

The QA job produces renders, a contact sheet, observation/coverage summary, geometry/material metrics, and a discrepancy record with severity, affected aspect, reference IDs, and suggested target. A future visual model receives only the building record, licensed references, cameras, renders, and evidence policy. It may propose discrepancies; it cannot silently relabel evidence or directly bless its own output.
