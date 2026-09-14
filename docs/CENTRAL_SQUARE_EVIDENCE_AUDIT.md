# Central Square M6 evidence audit

Audit date: **2026-09-11**  
Target: `bgc_building_0014` — Central Square  
Outcome: **RECONSTRUCTION_READY_WITH_GAPS** for a medium-fidelity LOD1 representation of approximately 2025–2026 permanent architecture.

## Search and evidence inventory

The targeted pass searched the SSI operator and annual report, the Ayala cinema directory, the project consultant portfolio, contemporary reporting, OSM/Overpass records, Wikimedia Commons keyword/category/geographic discovery, and bounded web/video searches for all four sides, entrances, roof, and context. The reproducible Commons pass records 166 metadata candidates and downloaded zero image files.

Accepted package inventory:

- 5 authoritative or authoritative-role sources: OSM geographic records, SSI current property page, SSI 2015 annual report, I.A. Campbell project portfolio, and Ayala cinema directory;
- 7 reusable Commons visual references with explicit CC BY-SA 4.0 metadata;
- 6 research-only visual references from official, editorial, blog, and video pages;
- 5 unique exterior viewpoints, all directionally resolved;
- 17 total references and 21 source-linked observations after generation.

No reliable architect-issued drawing, floor plan, elevation, section, or survey was located. Search exhaustion is recorded as a remaining evidence gap, not proof that those records do not exist.

## Coverage and chronology

| Aspect | Coverage | Modeling consequence |
| --- | --- | --- |
| Overall massing | GOOD | Footprint-controlled box-like LOD1 mass is supported. |
| North / 30th Street | GOOD | Major opaque, glazed, recessed, and signage zones may be blocked in. |
| West / 5th Avenue | PARTIAL | Preserve broad composition; do not assert exact portals or mullion spacing. |
| South / High Street | PARTIAL | Preserve recessed retail edge and landscape relationship; simplify occluded bays. |
| East / service side | WEAK | Neutral massing-only treatment; no invented openings or loading geometry. |
| Entrances | PARTIAL | Recessed glazed placeholders only; hierarchy and exact portal geometry unresolved. |
| Roof | PARTIAL | Flat roof/parapet supported; omit fine plant and screens. |
| Materials | GOOD | Use coarse warm-neutral opaque, dark glazing/recess, and muted metal families. |
| Street context | GOOD | Major road/pedestrian/landscape relationships are supported. |

The time-state ledger spans 2014–2026. Architectural silhouette appears consistent across the accepted sequence, while tenants, murals, digital displays, event tents, and seasonal graphics vary. Model permanent architecture to approximately 2025–2026 and keep mutable graphics optional. The source-age distribution is stored in `timeline.json`.

## Resolved facts and preserved conflicts

- Identity, name, address context, and June 2014 opening are authoritative.
- OSM records an explicit 25.9 m height and a local footprint envelope of about 87.08 × 80.68 m; this is verified geographic data, not a surveyed measurement.
- Published descriptions agree on two basements and approximately four above-ground retail/cinema levels, but OSM records five building levels. Directory labels are not converted into geometry.
- The 2015 Commons reference is an interior atrium view and is not used as facade evidence.

## Remaining unknowns and stop rule

High/medium gaps are exact entrance hierarchy, east/service-side continuity, basement ramp/service access, and physical-storey mapping. Lower-priority gaps are exact mullion rhythm, roof plant/screens, and current tenant/campaign state. The package gives a conservative fallback for each unknown and explicitly prohibits invented architectural detail.

Further generic web searching is unlikely to change the LOD1 decision. Stop M6 here; resume evidence gathering only for a named gap, a newly supplied drawing, or user perimeter capture. Follow `USER_CAPTURE_REQUEST.md` for the shortest useful field pass.

## Handoff recommendation

Proceed to **M7 — medium-fidelity reference-grounded reconstruction** with Sol. Expected compute: **MODERATE**. Astra required next: **NO**. Validate the generated package before modeling and preserve all rights and uncertainty fields downstream.
