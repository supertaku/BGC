# M21 public realm

**Status: partial.** The deterministic generator `scripts/visual_detail/build_visual_detail.py` emits 38 tile-clipped surfaces across 6 tiles: {'PAVING_BORDER': 33, 'PARK_EDGE': 3, 'ZEBRA_CROSSING': 2}. The viewer merges each tile/material surface batch. Existing road and open-space surfaces remain in the base GLBs.

Grounded: mapped High Street pedestrian geometry and zebra-tagged crossings. Inferred: narrow visual border widths. Deferred: surveyed curbs, ramps, stairs, grades, amphitheater and water footprints. Rejected: fabricated height changes. Build passes; matched performance and detailed visual review remain open.
