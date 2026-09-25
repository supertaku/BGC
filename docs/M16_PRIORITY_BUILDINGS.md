# M16 — Priority building selection

Status: **PARTIAL.** Ranking and bounded selection are complete, but one selected target fails the evidence gate.

The deterministic pass in `scripts/reconstruction/prepare_m16_m17.py` ranked all 6,982 canonical entities using the existing processed geographic snapshot before researching any additional buildings. It retained each dimension separately: landmark importance, pedestrian and tour visibility, distinctiveness, current LOD2 error, identity, footprint, height, public-evidence proxy, and complexity. The scores are prioritization heuristics, not architectural facts. Its spatial proxy uses a fixed High Street corridor and may misrank buildings near other walking routes; review the [full ranking](../data/reports/m16-priority-ranking.json) before expanding the batch.

| Tier | Count | Intended treatment |
| --- | ---: | --- |
| A — landmarks | 4 | LOD1 candidate |
| B — important context | 37 | Selective LOD1 candidate |
| C — background | 6,941 | Stay LOD2 |

Ten targets were selected: four in wave A and six in wave B. Nine are `READY_WITH_GAPS`; Arthaland Century Pacific Tower is `NOT_READY` because its architect-published 136 m height conflicts with the 114.7 m OSM envelope used by the draft. It remains in the audit but is excluded from future M17 batches until reconciled or replaced. Roof and entrances are weakly documented, and facade coverage is uneven. The [selection report](../data/reports/m16-selected-buildings.json) records entity ID, tier, rationale, visibility, readiness, complexity and target LOD.

| Wave | Target | Tier | Archetype |
| --- | --- | --- | --- |
| A | One Bonifacio High Street | A | Mixed-use podium |
| A | The Suites at One Bonifacio High Street | A | Podium tower |
| A | Philippine Stock Exchange | A | Office landmark |
| A | Arthaland Century Pacific Tower | A | Office tower |
| B | Shangri-La at the Fort | B | Hotel/podium tower |
| B | The Mind Museum | B | Cultural/irregular |
| B | Maybank Performing Arts Theater | B | Performing arts |
| B | High Street South Corporate Plaza | B | Office tower |
| B | Two Maridien | B | Residential tower |
| B | The Verve Residences One | B | Residential tower |

The original seven approved LOD1 assets were preserved. No city-wide height correction or city-wide image research was performed. Ranked height uncertainty is retained in the machine report; selected height conflicts require resolution before M17 visual approval. Official and project imagery is `RESEARCH_ONLY`, not a texture or redistributable asset.

Gate interpretation: the whole-city ranking and nine bounded evidence packages pass preparation, but the requested rule to replace `NOT_READY` targets was not met. Thus M16 remains partial. `READY_WITH_GAPS` permits conservative reconstruction attempts, but does **not** establish that generic generated geometry matches references. The later M17 visual gate remains independent.
