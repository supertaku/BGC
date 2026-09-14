# Data architecture

## MVP storage decision

Use versioned JSON and GeoJSON files through MVP-A. The datasets fit comfortably in source-controlled files, are inspectable without a service, and match the deterministic Blender pipeline. Add SQLite only when cross-entity queries, concurrent edits, or reference counts become painful. Do not add PostgreSQL/PostGIS for MVP-A or the first whole-city skeleton.

The canonical machine-readable definitions are:

- `data/geographic/*.geojson`: scope and pilot polygons in declared CRS.
- `data/raw/`: immutable cached source responses plus retrieval metadata and hashes.
- `data/processed/`: normalized, project-owned records in the local coordinate frame.
- `data/entities/reconstruction-model.schema.json`: lightweight entity/observation/asset/job contract.
- `data/sources/sources.json`: M5 access, license, attribution, authority, and cache-policy records (`data/entities/source-registry.json` remains the M1–M4 compatibility registry).
- `references/metadata/`: one metadata record per acquired reference; images remain separate and rights-gated.

Stable IDs use namespaces, for example `osm:way:242294490`, `source:osm`, `ref:commons:<pageid>`, `asset:tile:12:18:lod2`, and `job:generate:<input-hash>`. A generated asset records input IDs, source hashes, generator version, and metrics; a path alone is not provenance.

M5 adds project-owned real-world IDs such as `bgc_building_0014` and `bgc_complex_0001`. These are persisted in `data/entities/pilot-entities.json`; OSM feature IDs map to them and never substitute for them. Re-running the resolver reuses the mapping and appends new IDs rather than renumbering known entities.

## Entities

| Entity | Required MVP fields | Notes |
| --- | --- | --- |
| Building | stable ID, footprint geometry, observations for name/height/levels, tier, status, source IDs, coverage | Holes and building parts must remain distinguishable when ingestion is expanded. |
| Road | ID, centerline/area, class, width observation, surface, source IDs | Width defaults are estimates, never verified road dimensions. |
| Path | ID, geometry, subtype, accessibility tags, source IDs | Retain pedestrian/cycle distinctions. |
| OpenSpace | ID, polygon, subtype, vegetation/land-cover observations | Parks and landscaped medians are not interchangeable. |
| POI | ID, point/polygon, category, name, entity link | POIs can identify a building without defining its geometry. |
| ReferenceImage | ID, source URL, author, license, capture time, geolocation, direction, target IDs, file hash | No image enters the reusable library without a rights decision. |
| Observation | entity, field, value, evidence class, confidence, source IDs, time, notes | Multiple competing observations are allowed; resolution is explicit. |
| Source | URL/dataset ID, license, attribution, retrieval time, CRS, content hash | Required for every external claim. |
| Asset | entity IDs, LOD, path, generator version, geometry/material/texture metrics | Generated artifacts can be deleted and recreated. |
| ReconstructionJob | type, inputs, outputs, tool version, status | Input hashes make regeneration decisions deterministic. |

## Evidence and confidence

The machine enum is deliberately more specific than a single “verified” label:

| Class | Meaning | Example |
| --- | --- | --- |
| `VERIFIED_GEOGRAPHIC` | Directly present in a cited geographic dataset | OSM building footprint or tagged height. |
| `VERIFIED_PHOTOGRAPHIC` | Directly visible in one or more identified images | Window-bay count on the photographed north facade. |
| `INFERRED` | Reasoned from related evidence, not directly visible/measured | Likely continuation of a facade rhythm around a partly visible corner. |
| `ESTIMATED` | Numeric/category approximation with a documented method | `building:levels × 3.2 m`. |
| `PROCEDURAL` | Deliberate filler chosen by a generator | Generic rear facade where references are absent. |
| `UNKNOWN` | No defensible value | Roof plant layout with no aerial evidence. |

Confidence is a 0–1 assessment of the observation, not of the source in general. The pipeline may use a lower-confidence value, but it must preserve the class and method. No normalization step upgrades `ESTIMATED`, `INFERRED`, or `PROCEDURAL` to verified.

## Reference coverage

Coverage is stored per building and aspect: north, south, east, west, entrance, roof, street context, and aerial context. Each aspect has a rating, reference IDs, and notes.

| Rating | Operational definition |
| --- | --- |
| `NONE` | No usable reference for the aspect. |
| `WEAK` | Oblique, distant, outdated, occluded, or single ambiguous view. |
| `ADEQUATE` | At least one usable view with enough detail for massing/material decisions, but not robust correction. |
| `GOOD` | Multiple complementary or high-quality views support geometry and material QA. |

Ratings are about decision coverage, not image count. Duplicate frames from one sequence do not automatically improve a rating. Capture date, direction, occlusion, resolution, licensing, and whether the building has changed all affect the result. The candidate experiment demonstrates why: two Commons searches hit 500 nearby files while returning many vehicle/event photos.

## Fidelity tiers

- **Tier C — background:** default. Footprint plus evidence-based or estimated height, shared material family, silhouette-focused LODs. Assign automatically unless another criterion promotes it.
- **Tier B — approachable:** visible from pilot navigation routes, meaningful ground-floor frontage, sufficient `ADEQUATE` facade/entrance coverage, or important to spatial recognition. Procedural base plus selective corrections.
- **Tier A — landmark:** unique silhouette or civic/navigation significance, high expected screen time, and enough evidence to justify custom work. Manual approval is required; visual prominence alone is not sufficient.

Promotion scoring may rank route proximity, projected screen size, POI/landmark status, architectural distinctiveness, and coverage. Low coverage should create a research task rather than produce fabricated detail. Tier A should remain a small set.

## Source strategy

| Source | Reliable use | Access / metadata | Rights decision |
| --- | --- | --- | --- |
| OpenStreetMap | Footprints, names, roads, paths, land use, parks, POIs, some levels/heights/addresses | Overpass/API; stable element IDs and tags, uneven completeness | ODbL 1.0; show “© OpenStreetMap contributors” and comply with share-alike requirements for publicly used derived databases. Do not use public tile servers as a bulk data API. |
| Official government/BCDA/FBDC material | Scope, plan intent, identity, authoritative context | PDFs/pages; often not machine-readable | Research/reference unless explicit reuse rights exist; do not redistribute embedded media by assumption. |
| Wikimedia Commons | Openly licensed candidate photos and some maps | MediaWiki API; `imageinfo` `extmetadata` exposes author/license fields; geolocation and capture date optional | Check every file's license and credit requirements; record author, title, source, license and modifications. |
| Mapillary | Street-level sequences, position, capture time, compass/panorama metadata | Graph API requires an access token | Contributed imagery is described by Mapillary as CC BY-SA; retain image/contributor links and review share-alike implications before derivatives. |
| Official building/developer sites | Building identity, current marketing views, named features | Web pages; weak camera/geolocation metadata | Normally copyrighted. Use for factual observation/research, not bulk acquisition or redistribution without permission. |
| Future user photography | Targeted missing facade/roof/context coverage | Submission form should require target, position, direction, date, license/consent | Best controllable source if consent, privacy, attribution, and reuse scope are explicit. |

Primary rights references: [OSMF attribution guidance](https://osmfoundation.org/wiki/Licence/Attribution_Guidelines), [Wikimedia Commons reuse guidance](https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia), [Commons API license metadata note](https://commons.wikimedia.org/wiki/Commons:Credit_line/en), and [Mapillary CC BY-SA guidance](https://help.mapillary.com/hc/en-us/articles/115001770409-CC-BY-SA-license-for-open-data).

## Acquisition rules

1. Query metadata first; download only references assigned to a target/aspect gap.
2. Cache raw geographic responses and hashes. Refresh only through an explicit `--force` operation and review the diff.
3. Store original source geometry and CRS; transformed coordinates are derived data.
4. Never scrape uncontrolled copyrighted galleries.
5. Store a rejection reason (`irrelevant`, `license_unknown`, `outdated`, `duplicate`, `bad_pose`) so rejected results are not repeatedly re-analyzed.
6. Entity matching records candidate IDs, method, and confidence; names alone are insufficient.
