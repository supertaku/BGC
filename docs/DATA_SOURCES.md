# Data sources and provenance

An immutable OpenStreetMap snapshot for the canonical High Street central-core pilot is now the grounded geographic input. It is licensed under ODbL 1.0 and retains its complete query, boundary/query/raw hashes, retrieval timestamp, endpoint, and attribution sidecar. The processed outputs preserve source IDs and evidence status. No photographic files have been downloaded.

The Wikimedia Commons proof of concept stores metadata-only discovery results, including candidate and rejection records. Candidates are not accepted visual evidence until identity, orientation, relevance, and rights are reviewed. The Mapillary integration boundary is implemented but currently reports `BLOCKED_CREDENTIALS` when no access token is present; this does not block the geographic pipeline.

`data/entities/source-registry.json` is the canonical source inventory. The full geographic, visual-reference, licensing, evidence, and coverage strategy is in `docs/DATA_ARCHITECTURE.md`.

Every record must retain source URL or dataset identifier, license, retrieval date, original CRS, transformation history, entity-match confidence, and field-level evidence classification. Derived records and assets point back to source IDs and content hashes.
