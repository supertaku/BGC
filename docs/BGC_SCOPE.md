# BGC scope and pilot selection

## Geographic interpretation

Three different concepts must not be conflated:

1. **Official/legal boundary.** Administrative Order No. 269 (1996) confirms an official Fort Bonifacio Master Development Plan. BCDA publications describe the initial BGC development as 240 hectares, but no authoritative, reusable machine-readable legal polygon was located during this phase. The official/legal boundary therefore remains **unknown in coordinate form**.
2. **Commonly understood BGC.** Public maps and district material generally describe the dense district around the 5th/11th Avenue and 26th/32nd Street city-center grid, plus surrounding Uptown, institutional, Market! Market!/Serendra, and southern areas. This is a social/planning extent, not a cadastral claim.
3. **Project working boundary.** The repository uses `data/geographic/bgc-working-boundary.geojson`. It is an **estimated project polygon**, versioned and reproducible, suitable for queries and tiling. It must never be labeled an official boundary. Replace it only when an authoritative boundary with usable rights and provenance becomes available.

The current working polygon measures approximately 472 hectares after projection. It deliberately covers the broader commonly mapped district and is larger than BCDA's reported 240-hectare first-phase development. The difference is another reason it must not be presented as the official boundary. Its vertices are WGS84 (`EPSG:4326`); all processing converts them to the project CRS before measurement.

Sources: [BCDA 2014 Annual Report](https://www.bcda.gov.ph/sites/default/files/2021-09/2014%20Annual%20Report.pdf), [Administrative Order No. 269](https://issuances-library.senate.gov.ph/executive-issuance/administrative-order-no-269-s-1996), and the [BCDA/FBDC master-plan FOI record](https://www.foi.gov.ph/requests/bgc-master-development-plan/).

## Pilot candidates

Candidate polygons are stored in `data/geographic/pilot-candidates.json`. Metrics below were measured on 2026-09-10 by `scripts/geography/assess_pilot_candidates.py` using one union-area Overpass request and Wikimedia Commons geosearch. Counts are coverage indicators, not statements of ground truth. OSM elements can overlap categories; Commons results can be irrelevant to architecture.

| Candidate | Approx. dimensions | OSM buildings (named) | Height / level tags | Pedestrian / vegetation / furniture features | Commons signal | Assessment |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| High Street central core | 494 × 419 m | 32 (27) | 10 / 14 | 244 / 132 / 26 | API limit reached | Best technical cross-section: dense promenade detail, retail blocks, office massing, parks, ordinary intersections, and mixed heights. Raw photo results include irrelevant event/vehicle images, so per-facade review is required. |
| High Street east / Serendra edge | 456 × 424 m | 34 (16) | 17 / 20 | 86 / 46 / 9 | 75 files | Strong retail/residential context and pedestrian activity, but less mapped street detail and a difficult mall/compound edge make the first benchmark less balanced. |
| High Street west / cultural edge | 467 × 447 m | 35 (27) | 25 / 29 | 175 / 80 / 10 | API limit reached | Best height completeness and strong landmark/open-space content, but landmark massing dominates and could hide weaknesses in ordinary storefront generation. |

The Commons count reaching 500 is a query-limit signal, not `GOOD` coverage. Sample results include vehicle and event photography. This empirically supports the coverage model in `docs/DATA_ARCHITECTURE.md`.

## Recommended pilot

**Bonifacio High Street central core**, approximately 5th–9th Avenues and 28th–32nd Streets.

The canonical MVP polygon is `data/geographic/pilot-boundary.geojson`: west/east longitudes 121.04750/121.05205 and south/north latitudes 14.54865/14.55240. Projection testing measures it at approximately 494.0 × 419.2 metres and 20.35 hectares. The older `pilot-zone.geojson` is retained only as the planning-phase compatibility record. The wording is approximate because road names and parcel edges are not the polygon's legal basis.

Why this pilot:

- It tests both recognizable architecture and ordinary repeatable fabric.
- It includes low-rise retail, office buildings, parking structures, roads, intersections, a pedestrian spine, vegetation, and street furniture.
- Its OSM footprint coverage is already sufficient for a real-data massing experiment, while incomplete height data forces the evidence model to work honestly.
- It is compact enough for fixed-camera QA and a single initial web asset, but large enough to expose draw-call, material, navigation, and reference-matching issues.
- It does not win merely by spectacle; it is the broadest reconstruction benchmark of the three.

## Current real-data evidence

The immutable 2026-09-10 Overpass snapshot contains 883 elements. Full normalization emits 31 building outlines, 8 building parts, 88 roads, 269 pedestrian/path features, 21 open-space areas, and 383 POIs. Footprints are `VERIFIED_GEOGRAPHIC`; 17 records have explicit OSM height tags, 4 use an `ESTIMATED` levels heuristic, and 18 use a visibly documented `PROCEDURAL` fallback.

This is the first reproducible real BGC pilot scene in the pipeline. It is not detailed reconstruction and should not be judged as one.
