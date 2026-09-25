# M16R evidence and scope recovery

Status: **PASS for the revised one-building calibration batch**. The prior nine `READY_WITH_GAPS` labels were based largely on reference presence and do not satisfy visual reconstruction readiness. `data/reports/m16-selected-buildings.json` separates the ten original candidates from the final evidence-ready batch: PSE Tower only. Nine candidates are deferred; none has been replaced or visually approved.

`scripts/reconstruction/evidence_gate.py` requires explicit ratings for identity, footprint, height, massing, principal and secondary facades, roof, entrance, and materials. Identity, footprint, height decision, massing, principal facade, and two distinct inspected camera-matchable viewpoints must pass. Roof and entrance may remain weak or absent. `evidence_coverage.json` in each package stores the reviewed basis; a URL count never supplies a rating.

| Candidate | M16R finding | Next evidence work |
| --- | --- | --- |
| PSE Tower | Architect confirms 30 stories, inflected glazed frontpiece and deep vertical ribs. OSM provides the 131 m mapped height and polygon parts. Two distinct architect photographs show the southeast principal side from street and elevated positions; camera matches are approximate (0.55/0.60 confidence). | Calibrate the OSM part interpretation and massing against both views. |
| The Suites | Architect confirms glass and masonry, gentle curvature, horizontal bands, balconies and street courtyard. | Locate a second camera-matchable view and interpret curvature against the footprint. |
| Arthaland Century Pacific Tower | SOM publishes 136 m and 32 stories; OSM retains 114.7 m as conflicting geographic data. Reconstruction envelope is 136 m from SOM. | Match facade and upper silhouette views. The 114.7 m source observation remains in `observations.json`. |
| One Bonifacio High Street | OSM way `1078392706` has `shop=mall`, `building=commercial`, a 12,248.33 m² footprint and a **procedural** 12 m height. Spatial intersection covers 98.9% of The Suites footprint and 99.5% of the PSE footprint. It is not a safe standalone mall mesh. Handel's project includes residential, retail and office components. | Verify the actual retail component boundary and get podium-specific views, or replace this candidate. |
| Six Wave B candidates | Existing reference pairs do not establish aspect-level massing and facade coverage. | Audit in small groups only after Wave A calibration. |

The initial preparation script now preserves recovered packages and selections on rerun. `apply_m16_recovery.py` is the idempotent source-fact update; it does not build or publish assets. It removes generic horizontal facade bands from future M17 package builds and marks old camera presets as unmatched diagnostics.

The overlap is reproducible with `.venv/Scripts/python.exe scripts/reconstruction/verify_obhs_scope.py`; results are in [m16-obhs-scope.json](../data/reports/m16-obhs-scope.json). It verifies OSM polygon overlap, not the physical retail boundary.

Sources: [Handel PSE](https://handelarchitects.com/project/philippine-stock-exchange), [Handel Suites](https://www.handelarchitects.com/project/the-suites-at-one-bonifacio-high-street?pagi=residential), [SOM ACPT](https://www.som.com/projects/arthaland-century-pacific-tower/), [Handel One Bonifacio project](https://handelarchitects.com/latest/one-bonifacio-high-street-in-manila-breaks-ground). Source photographs remain research-only and are not stored in the repository.
