# Reference rights policy

This is project policy, not legal advice. When license facts are incomplete or conflicting, preserve uncertainty and obtain a human/legal review before reuse.

## Discovery is not reuse

The project tracks these dimensions separately:

- `DISCOVERED`: a source item was found;
- `VIEWABLE_FOR_RESEARCH`: a person or agent may inspect the source page for research;
- `LOCAL_COPY_ALLOWED`: the project has a basis to store the file;
- `DERIVATIVE_USE_ALLOWED`: transformations such as textures or traced detail are permitted;
- `COMMERCIAL_USE_ALLOWED`: the stated license permits commercial use;
- `REDISTRIBUTION_ALLOWED`: the original or derivative may be shipped;
- `ATTRIBUTION_REQUIRED`: release credits must name the creator/source/license;
- `SHARE_ALIKE_REQUIRED`: derivatives or collections may carry reciprocal obligations.

No single `copyright_ok` flag is used. Public accessibility does not establish permission.

## Source rules

Wikimedia Commons files are reviewed independently. The pipeline retains file page ID, page URL, SHA1, creator, credit, explicit license name/URL, attribution, ShareAlike, and review time. Missing creator data for an attribution license, missing/malformed terms, or an unrecognized license produces `REVIEW_REQUIRED`. Presence on Commons alone is insufficient.

Official government, developer, operator, directory, and ordinary website pages may support factual observations and identity. Unless the page gives an explicit compatible media license, their photographs are `RESEARCH_ONLY`: do not download them into the repository, transform them into textures, bundle them in the website, or redistribute them.

Public-domain claims are stored as claims with source provenance. A questionable or conflicting claim stays `REVIEW_REQUIRED`. CC BY material requires attribution. CC BY-SA material requires attribution and a release-time ShareAlike analysis. License/version URLs and modification notes must survive export.

User captures are first-class future sources but require an explicit contributor grant/consent, privacy review, creator credit, capture time, GPS, orientation/device metadata where available, original hash/path, derived thumbnail link, manual notes, and entity links.

Mapillary remains metadata-only and `BLOCKED_CREDENTIALS` until an explicitly authorized token is supplied. Provider/API terms and derivative/redistribution implications must be reviewed before local imagery storage.

## Storage and distribution

Default acquisition is metadata and permitted thumbnails. Full-resolution downloads occur only when the source permits them and a reconstruction decision needs the asset. Large binaries never enter JSON or SQLite. Source-native IDs, canonical URLs, and source SHA1 are the preferred deduplication keys.

Before a public release, assemble credits for every bundled asset, verify license compatibility and modification notices, review ODbL obligations for distributed geographic databases, and fail the release if required provenance is missing.
