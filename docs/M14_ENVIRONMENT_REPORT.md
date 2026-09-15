# M14 Environment Report

Status: **PASS** for the available source-grounded environment scope.

The existing immutable OSM snapshot already contained usable micromapped street objects, so no supplemental acquisition or visual-reference search was performed. The generated runtime includes 452 `VERIFIED_GEOGRAPHIC` positions: 364 trees, 4 street lamps, 18 benches, 54 bollards, 6 waste bins, and 6 shelters. Procedural instances are zero.

Every instance has one deterministic 250 m tile owner and follows that tile's active lifecycle. Runtime rendering groups by tile and asset type with one shared low-poly geometry/material pair per type. The whole city has 52 nonempty instanced draw groups; the observed dynamic High Street state had 28. Quality controls are OFF, LOW (trees and lamps), and FULL (all six categories).

Automated QA verifies deterministic bytes, unique ownership, and point containment within the owner tile. All objects use exact project-local coordinates with ground-relative transforms. Because the objects are directly mapped, a tree or other item overlapping a mapped road/building is not silently relocated; its source location remains authoritative and reviewable.

The principal weakness is source density: four mapped street lamps and six shelters cannot describe complete district coverage. The generic geometry communicates category and location only, not verified appearance. Machine-readable evidence is in `data/reports/m14-environment.json`.
