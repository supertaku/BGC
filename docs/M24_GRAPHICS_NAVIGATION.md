# M24 graphics and navigation

Explore Help exposes exactly: Left drag â€” Pan; Right drag â€” Look around; Hold Right Mouse + WASD â€” Fly; Scroll â€” Zoom.

Right drag changes yaw/pitch at a fixed camera position, clamps pitch to Â±85 degrees and removes roll. WASD moves horizontally only while the right pointer is held, normalizes diagonals, and uses delta time and altitude-based speed. Left drag pans on a horizontal plane; zoom follows the viewing direction. World bounds, terrain clearance and a 2800m ceiling constrain translation. Pointer capture, cancel, lost capture, window blur and UI focus release active controls. Tour mounts no Explore/Walk input controller; Walk retains PointerLock and GroundSampler.

Performance, Balanced (Recommended), and Quality change DPR, shadows, fine-detail range/density, vegetation density, art range and water roughness. Identity geometry, major signs and terrain remain enabled for every preset. Presets are validated from `?graphics=` first, then `bgc.graphics.v1` localStorage, then Balanced. The radio dialog supports keyboard navigation, Escape, focus trapping and focus restoration. Changing settings does not remount Canvas or reset navigation, camera or Search.

The pure logic and configuration tests pass. Browser testing confirms keyboard profile selection, URL update, camera preservation, Escape, focus trapping/restoration, exact Help text, left pan, view-direction zoom and Search interruption without restart. The full seven-stop Tour completed without visibility gaps or repeated requests. Full held-right-button feel and profile visual acceptance remain AWAITING_USER_TEST.

Benchmark routes are debug-only, derived from mapped/constructed walking surfaces, use one shared 20-second clock (5-second warmup + 15-second sample), and stop at its end. Walk reports cumulative travelled distance rather than straight-line displacement. Background, throttled, changed-viewport/DPR, runtime-error and incomplete-walk runs are invalid.
