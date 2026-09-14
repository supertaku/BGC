# Pilot height evidence update

Audit date: **2026-09-11**.

| State | Previous | After M5 identity enrichment |
| --- | --- | --- |
| VERIFIED_GEOGRAPHIC | 17 | 17 |
| ESTIMATED | 4 | 4 |
| PROCEDURAL | 18 | 18 |
| UNKNOWN | 0 | 0 |
| CONFLICTED height | 0 | 0 |

All 18 procedural-height geographic features were checked opportunistically during identity, official-source, and direct-Wikidata enrichment. No defensible explicit height or floor count surfaced for those features, so none was upgraded. The structured check list is `data/references/procedural-height-checks.json`.

Canonical entities with explicit tower/podium parts use the maximum explicit OSM part height for reconstruction-readiness summaries while preserving every component height. This does not modify Blender geometry or the normalized geographic source.

One non-height conflict is retained: W Group describes W Global Center as seven storeys while OSM records `building:levels=8`. The project preserves both statements in `data/references/conflicts.json`; neither silently overwrites the explicit OSM height value.
