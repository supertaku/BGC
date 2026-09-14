# Entity structure audit

Audit date: **2026-09-11**.

| Measure | Result |
| --- | --- |
| Raw geographic building records | 39 |
| Building outlines | 31 |
| Building parts | 8 |
| Canonical building/structure entities | 31 |
| Building complexes | 2 |
| Building parts resolved | 7/8 |
| Unresolved building fragments | 1 |

One unnamed office outline (`osm:way:1071370327`) is merged into the Mariano K. Tan Center entity because it is wholly contained by the named outline and both contain the same explicit building part. This is an entity-layer decision only; neither source polygon is changed. The nested Bench footprint remains a child entity of B:5 pending building-versus-tenant review. Two roof multipolygons remain separate unresolved structures. The western `osm:way:469908149` building part has no containing in-pilot outline and remains an unresolved fragment, likely because its parent lies beyond the clip.

Complex records are separate from physical buildings: Bonifacio High Street and High Street South. Membership is evidence-scored and does not merge member geometry.

Machine-readable evidence: `data/entities/pilot-entities.json` and `data/review/entity-match-review.json`.
