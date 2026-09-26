# M23R–M24 — BGC Visual Fidelity Completion, Persistent Building Identity, Explore Navigation & Graphics Settings

## Mission

Continue directly from the existing M23 implementation.

Do **not** restart M23 from scratch.

The purpose of this corrective/completion phase is to solve the visual and usability problems found during user testing while finishing the major incomplete pieces from the original M23 brief.

The final BGC viewer should satisfy six major goals:

```text
1. No facade flickering or z-fighting.

2. Building visual identity must not disappear
   simply because the camera moves farther away.

3. Every BGC building must have some intentional facade design,
   even when exact architectural evidence is unavailable.

4. High Street, roads, parks and other public environments
   must be substantially more complete.

5. Verified building/company/store names and logos
   must appear where they exist in the real BGC.

6. Explore navigation and graphics settings
   must be simple and user-friendly.
```

This is still a low-to-mid fidelity reconstruction.

Do not pursue photorealism.

---

# 1. Repository state

Inspect the actual repository before modifying anything.

At the time of this review, the latest pushed M23 work was based on the current `main` after the comprehensive M23 implementation.

Repository state is authoritative.

Record:

```text
branch

HEAD

git status

Node/npm

Three.js

R3F

Drei

Blender

Python

current M23 package count

current tile count

current canonical building count

current landmark count

current signs/art counts
```

Current known project scale:

```text
canonical buildings:
6,982

render volumes:
7,120

world tiles:
94

M23 packages:
108

M23 landmark packages:
31

existing M23 signs:
40

approved pre-M23 LOD1 assets:
7
```

Verify these values from the repo before using them.

---

# 2. Existing M23 work to preserve

Preserve working M23 systems:

```text
108 package system

terrain-aware Walk

GroundSampler

High Street Central terrain

public-realm generation

street-detail packages

park packages

LOD1-Lite work

hero landmark packages

reference database

M23 deterministic generation

Search

Tour

street locator

M19D tile stability

last-good-visible tiles

per-tile Suspense

per-landmark Suspense

current public-realm exclusion logic
```

Do not regress these while fixing fidelity.

---

# 3. User-reported defects

Treat these as hard requirements.

## Defect A

```text
Building facades visibly flicker.
```

## Defect B

```text
Detailed building designs disappear at distance
and become simple again.
```

## Defect C

```text
Many buildings still look like plain generic boxes.
```

## Defect D

```text
Parts of the land/public realm are visually missing,
especially around Bonifacio High Street.
```

## Defect E

```text
Roads and other environments still need substantially
more visual detail.
```

---

# 4. Additional requirements

Add:

```text
verified company/building/store names and logos

new Explore camera controls

simple Graphics Settings UI

Explore-control instructions in Help
```

---

# 5. Current architecture findings

Before implementing, verify these findings against actual code.

## 5.1 M23 proximity activation

Current M23 packages are activated approximately using:

```text
camera height < 650 m

AND

distance to stream anchor
<
package activation_m + hysteresis
```

with many activation distances around:

```text
150–240 m
```

This means visual identity itself is being treated as near-range detail.

That must change.

---

## 5.2 Current facade fallback

When an M23 package becomes inactive:

```text
specific building design disappears
↓
base LOD2 representation returns
```

This directly causes:

```text
designed building
→ move away
→ generic building
```

This is no longer acceptable.

---

## 5.3 Current base city

The base building generator still primarily uses simple type-based materials such as:

```text
neutral

residential

retail

office
```

Most of BGC therefore remains intentionally simple.

M23 currently solves only a small subset.

---

## 5.4 Current facade geometry

M23 builds building massing plus additional facade:

```text
bands

panels

screens

windows

frames

etc.
```

Some of these surfaces are placed very close to another surface.

This creates possible depth competition.

---

## 5.5 Current material behavior

M23 currently creates materials globally using:

```text
THREE.DoubleSide
```

even for opaque building facades.

That is unnecessary for most buildings and can exacerbate visual ambiguity.

---

## 5.6 Current depth range

Canvas currently uses approximately:

```text
near = 0.1

far = 20,000
```

That is a very large depth ratio for a district-scale environment.

It should be reviewed.

---

## 5.7 Current art/signage

Packages can contain:

```text
signs[]

art[]
```

but runtime currently effectively renders:

```text
signs only
```

and limits display approximately to:

```text
first 3 signs per package
```

Art rendering must be finished.

---

# PART I — RENDER CORRECTNESS

# 6. Phase M23R-A — Eliminate facade flickering

Do this before adding more facade detail.

The rule is:

```text
do not hide z-fighting with prettier materials
```

Fix the geometry/depth problem.

---

# 7. Build a facade overlap validator

Create a validation tool that detects:

```text
exact duplicate triangles

coplanar facade surfaces

near-coplanar surfaces

overlapping facade panels

duplicate shell faces

thin surfaces embedded inside shell

transparent surfaces occupying same plane
```

Suggested warning threshold:

```text
surface separation < 0.02 m
```

for unrelated opaque layers.

Use sensible tolerance based on geometry scale.

---

# 8. Classify overlap severity

Output:

```text
EXACT_DUPLICATE

COPLANAR

NEAR_COPLANAR

INTENTIONAL_OVERLAY

CLEAR
```

Do not treat all close geometry as invalid.

Example:

```text
glass panel 0.10 m outside concrete shell
→ valid

two wall faces at identical location
→ invalid
```

---

# 9. One authoritative shell

Every detailed building should have one authoritative exterior shell.

Avoid:

```text
full generic building shell
+
full detailed building shell
```

occupying almost the same space.

Use either:

```text
A. detailed building replaces generic shell
```

or:

```text
B. decorative facade elements clearly project
   outside the shell
```

Never two nearly identical opaque shells.

---

# 10. Facade separation rules

Use actual physical depth.

Suggested ranges:

```text
glass skin:
0.05–0.15 m outside structural shell

facade band:
0.10–0.40 m

vertical fin:
0.15–0.80 m

screen:
0.15–0.60 m

balcony:
actual projected slab depth

sign:
0.03–0.10 m from facade
```

These are rendering/visual rules, not survey claims.

---

# 11. Material-side rules

Change general facade materials to:

```text
THREE.FrontSide
```

where appropriate.

Reserve:

```text
DoubleSide
```

for:

```text
thin signs

some foliage

single-plane art

special two-sided surfaces
```

Do not use `DoubleSide` globally.

---

# 12. Road/paving overlays

Use either:

```text
small physical elevation
```

or:

```text
polygonOffset
```

for:

```text
road paint

crosswalks

thin pavement markings
```

Do not use polygon offset as the primary fix for building facades.

---

# 13. Camera depth precision

Review actual required BGC distance.

Current far plane:

```text
20,000 m
```

is likely much larger than required for BGC.

Test reduced far ranges such as:

```text
6,000–10,000 m
```

using actual BGC extents/viewpoints.

---

# 14. Mode-specific near plane

Evaluate:

```text
Explore:
near ≈ 0.3–0.5 m

Tour:
near ≈ 0.3–0.5 m

Walk:
near ≈ 0.05–0.1 m
```

Use actual QA rather than blindly adopting these values.

---

# 15. Reverse depth buffer

Three.js supports `reversedDepthBuffer` when the browser/GPU exposes the necessary extension.

After geometry cleanup:

evaluate:

```text
reversedDepthBuffer: true
```

as an additional precision improvement.

Do not rely on it to fix broken geometry.

If unavailable:

fallback safely.

Do not enable logarithmic depth unless necessary because of its performance tradeoff.

---

# 16. Flicker acceptance

Require:

```text
0 known exact duplicate facade surfaces

0 unintended coplanar facade layers

0 visible facade shimmer
during representative Explore movement

0 visible facade shimmer
during Search camera transitions

0 visible facade shimmer
during Tour
```

Final visual confirmation:

```text
AWAITING_USER_TEST
```

---

# PART II — PERSISTENT VISUAL IDENTITY

# 17. Phase M23R-B — Redesign M23 detail persistence

Do NOT simply increase every activation radius.

That would load too much microdetail.

Instead split visual information into levels.

---

# 18. New M23 package layers

Upgrade M23 schema.

Suggested conceptual layers:

```text
IDENTITY

NEAR_DETAIL

MICRO_DETAIL

TERRAIN

SIGNAGE

ART
```

---

# 19. IDENTITY layer

Identity contains features that must remain visible from distance:

```text
building silhouette

podium/tower composition

major facade bands

major fins

major balcony rhythm

roof/crown

major material/color blocks

major building-name sign

major corporate roof/facade logo
```

This is relatively low-poly.

---

# 20. NEAR_DETAIL layer

Distance-activated:

```text
entrances

canopies

small balcony rails

storefront frames

minor fins

street-level facade panels

fine signage

public-realm furniture
```

---

# 21. MICRO_DETAIL layer

Quality-sensitive:

```text
drains

small utility objects

minor signs

tiny facade ornaments

dense landscape props

small art/detail
```

---

# 22. Identity persistence rule

For detailed/named landmarks:

```text
if its base tile is visible
→ identity should remain visible
```

Do not make identity depend on a 150–240 m distance ring.

---

# 23. Aerial behavior

Remove the current concept that all identity detail disappears merely because:

```text
camera.y >= 650
```

Instead:

```text
identity remains

near detail can disappear

microdetail disappears

terrain microdetail can disappear
```

---

# 24. Atomic handoff

When identity is needed:

```text
base building remains visible
↓
identity loads completely
↓
identity becomes READY
↓
hide corresponding base shell
```

When unloading:

```text
base replacement ready first
↓
then identity may hide
```

Never create:

```text
missing building

double building

generic flash
```

during handoff.

---

# 25. Explicit replacement mapping

Stop relying only on string conventions such as:

```text
m23:<id>
```

where possible.

Package should declare:

```text
replacement_entity_ids[]
```

Runtime should know exactly which base entities it replaces.

---

# 26. Prevent global geometry rebuilds

Current active package changes can cause all active package meshes to be re-merged.

Refactor so one package entering/leaving does NOT rebuild all M23 geometry.

Prefer:

```text
stable per-package cached geometry
```

or:

```text
stable per-zone batches
```

Then toggle visibility.

This reduces:

```text
frame spikes

visual popping

resource churn
```

---

# PART III — EVERY BUILDING GETS A DESIGN

# 27. Phase M23R-C — Universal facade system

The user requirement is:

```text
every building should have intentional visual design
```

This does NOT mean every building needs a researched bespoke model.

Use two systems:

```text
evidence-specific buildings
+
procedural designed buildings
```

---

# 28. Coverage target

Every valid canonical building should have:

```text
facade_style != NONE
```

Current approximate target:

```text
6,982 / 6,982 canonical buildings
```

subject to legitimate exclusions such as purely structural/non-building artifacts.

Any exclusion must be reported.

---

# 29. Procedural building categories

Classify buildings into:

```text
OFFICE

RESIDENTIAL

RETAIL

MIXED_USE

HOTEL

PARKING

CIVIC

EDUCATIONAL

MEDICAL

INDUSTRIAL/SERVICE

UNKNOWN
```

Use:

```text
OSM tags

name

levels

height

footprint shape

known entity type

stable deterministic hash
```

---

# 30. Base facade families

Create reusable visual families.

## Office

```text
CURTAIN_WALL_BLUE

CURTAIN_WALL_NEUTRAL

VERTICAL_FIN_OFFICE

HORIZONTAL_BAND_OFFICE

STONE_GLASS_OFFICE
```

## Residential

```text
BALCONY_GRID

GLASS_BALCONY

WINDOW_GRID_LIGHT

WINDOW_GRID_DARK

PODIUM_TOWER_RESIDENTIAL
```

## Retail

```text
GLAZED_RETAIL

STONE_RETAIL

OPEN_FRONT_RETAIL
```

## Parking

```text
LOUVER_PARKING

SCREEN_PARKING
```

## Civic/institutional

```text
STONE_CIVIC

GLASS_CIVIC

CONCRETE_CIVIC
```

---

# 31. Stable variation

Buildings should not all look identical.

Use a deterministic seed from:

```text
canonical entity ID
```

to select:

```text
material variant

window rhythm

vertical/horizontal emphasis

glass tint

roof treatment
```

The same build must always produce the same result.

---

# 32. Far-distance facade representation

Do not add thousands of tiny geometric windows.

Create efficient far-visible facade patterns using:

```text
shared procedural texture atlas
```

or another equally efficient strategy.

Preferred architecture:

```text
small number of shared materials

UV-mapped facade patterns

stable per-building atlas selection
```

---

# 33. Texture atlas

Generate project-owned facade atlases.

Examples:

```text
office-atlas

residential-atlas

retail-atlas

parking-atlas

institutional-atlas
```

Possible atlas cells:

```text
different glass grids

balcony patterns

stone/glass arrangements

panel grids
```

Keep them reusable.

No copyrighted facade photographs.

---

# 34. Ground-floor differentiation

Where plausible:

tall buildings should not look like the same facade down to the sidewalk.

Add simple:

```text
podium / ground-floor material zone
```

based on type.

For commercial/mixed buildings:

```text
more glazing at ground floor
```

where appropriate.

Mark as procedural when not visually verified.

---

# 35. Roof treatment

Every building should have intentional roof treatment:

```text
flat parapet

mechanical screen

simple crown

roof slab

residential roof edge
```

selected deterministically.

Do not add antennas/helipads unless supported.

---

# 36. Named buildings

The existing named interactive dataset contains roughly:

```text
263 named entities
```

Use these for higher-priority facade classification.

But physical signage must still be evidence-aware.

---

# 37. Bespoke buildings

Maintain specific persistent visual identity for:

```text
current 31 M23 landmark buildings
```

and continue expanding LOD1-Lite candidates where visual evidence exists.

The universal procedural facade is a fallback, not a replacement for accurate landmark design.

---

# PART IV — HIGH STREET PUBLIC REALM COMPLETION

# 38. Phase M23R-D — High Street hero ground replacement

The High Street core should no longer appear as:

```text
base ground
+
random detail patches
```

Build a complete hero public-realm surface system.

---

# 39. High Street coverage classes

Every non-building area inside the defined High Street hero boundary should be classified as one of:

```text
ROAD

PEDESTRIAN_PAVING

PLAZA

LAWN

PLANTER/SOIL

WATER

STAIRS

RAMP

SERVICE

UNKNOWN
```

---

# 40. Coverage analysis

Create a deterministic coverage validator.

Sample the hero zone using approximately:

```text
1–2 m grid
```

or equivalent polygon coverage.

Report:

```text
covered area %

unknown area %

holes > 4 m²

overlap area %
```

---

# 41. Hero-zone replacement rule

Inside High Street hero zones:

where a complete M23 surface exists,

do not render an overlapping base surface beneath it if that creates visible competition.

Use one authoritative surface.

---

# 42. High Street paving

Add recognizable:

```text
large paving slabs

paving joints

edge bands

plaza differences

accessibility surfaces where evidenced
```

Keep texture/material cost modest.

---

# 43. High Street landscape

Complete:

```text
tree rows

grass areas

hedges

shrub beds

planters

palm accents

tree grates

garden borders
```

Preserve verified mapped vegetation.

---

# 44. High Street furniture

Complete:

```text
benches

lamp families

bins

bollards

bike racks

wayfinding

outdoor dining

restaurant umbrellas

queue separators
```

Use evidence-constrained placement.

---

# 45. Accessibility detail

High Street references visibly show:

```text
ramps

railings

stairs

accessible routes
```

Continue expanding them where supported.

Do not invent exact slope percentages.

---

# 46. High Street Central

Preserve existing terrain system and improve missing areas.

Complete:

```text
grass terraces

stairs

ramps

handrails

amphitheater

plaza

feature gardens

water area

retaining edges

tree placement

path transitions
```

---

# 47. GroundSampler coverage

Walk must follow:

```text
every major High Street Central ramp

major terrace

major stair transition
```

Use smoothed invisible collision ramps on stairs if needed.

---

# PART V — ROAD AND STREET ENVIRONMENT

# 48. Phase M23R-E — RoadDetail system

Existing road geometry is too simple.

Add visual structure without rebuilding road GIS.

---

# 49. Use existing OSM data

The project already stores useful road metadata such as:

```text
class

width

lanes

surface

centerlines
```

Use these.

---

# 50. Lane markings

Generate when supported:

```text
center lines

lane dividers

dashed separators

edge lines

stop bars

turn arrows
```

Do not add lane divisions where lane count is unknown unless there is strong visual evidence.

---

# 51. Crosswalks

Use mapped crossings and current crossing evidence.

Add:

```text
zebra bars

stop line

curb-ramp relation
```

Avoid arbitrary intersection crosswalk generation.

---

# 52. Bike lanes

BGC currently confirms dedicated bike lanes and racks.

Support:

```text
painted lane

protected lane

bollard separators

bike symbol

bike rack
```

based on actual route evidence.

---

# 53. Curbs

Major pedestrian zones and important roads should gain:

```text
curb

gutter

curb ramp

median edge
```

Do not generate high-poly curbs citywide unnecessarily.

---

# 54. Drainage

Add reusable:

```text
storm inlet

drain grate

manhole

utility cover
```

at evidence-informed/inferred intervals.

Keep these MICRO_DETAIL so graphics presets can reduce them.

---

# 55. Traffic furniture

Add where supported:

```text
traffic signals

pedestrian signals

street-name signs

direction signs

parking signs

lane separators

bollards

road barriers
```

---

# 56. BGC bus infrastructure

BGC officially operates fixed-route internal buses.

Improve:

```text
bus shelter

stop sign

route panel

bench

queue edge
```

where current stop locations are known.

---

# 57. Ordinary sidewalks

Outside hero zones, improve ordinary BGC sidewalks with cheap visual cues:

```text
paving joints

curb differentiation

tree strip

occasional grates

pedestrian crossings
```

BGC design guidance emphasizes integrated pedestrian routes, arcades, greenways and sheltered storefront treatment.

---

# PART VI — COMPANY NAMES, BUILDING NAMES AND LOGOS

# 58. Phase M23R-F — Complete Signage/Brand Identity system

Do not bake tenant/company logos permanently into building geometry.

Use a separate identity layer.

---

# 59. Upgrade SignageAnchor

Extend current schema to include:

```text
id

building_id

facade

position

rotation

physical_width_m

physical_height_m

sign_type

display_text

logo_asset

logo_variant

source_url/source_id

source_type

grounding

verified_visible

current_as_of

rights_status

visibility_priority

distance_class
```

---

# 60. Sign types

Support:

```text
BUILDING_NAME

CORPORATE_LOGO

CORPORATE_NAME

MALL_NAME

STORE_LOGO

STORE_NAME

HOTEL_NAME

INSTITUTION_NAME

PARK_SIGN

WAYFINDING
```

---

# 61. Current sign limitation

Remove the runtime limitation equivalent to:

```text
signs.slice(0, 3)
```

Render signs based on:

```text
visibility priority

graphics profile

distance
```

not array order.

---

# 62. Permanent identity signs

Keep visible at long distance when physically large:

```text
tower crown names

major facade company names

mall identity

hotel identity

major institutional name
```

---

# 63. Near-only signs

Distance-cull:

```text
small storefront logos

restaurant signs

small tenant names

wayfinding
```

---

# 64. Current BGC retail directory

Use the current official BGC district directory as a primary source for High Street/One Bonifacio/Central commercial identity.

At review time it contains roughly:

```text
159 directory entries
```

with the shop directory returning roughly:

```text
71 shopping entries
```

Do not hard-code these counts.

Snapshot the current data during the build.

---

# 65. Tenant mapping

For each current directory entry:

record:

```text
brand

venue

floor/location

current_as_of

source
```

Then determine:

```text
EXTERIOR_VISIBLE

INTERIOR_ONLY

UNKNOWN
```

Only `EXTERIOR_VISIBLE` should normally become facade signage.

---

# 66. Office/company signage

For office towers:

perform targeted research only when a company logo/name is visibly mounted on the building.

Sources:

```text
official company website

official building/property website

official developer

official press/media page

current reusable street imagery
```

Do not infer office logos merely because a company leases space.

---

# 67. Logo assets

Actual graphic logos may be used only from:

```text
official brand asset/media kit

official public source

appropriately licensed reusable asset
```

Otherwise render:

```text
company name as text
```

instead of recreating the trademark from memory.

---

# 68. Logo texture handling

Use:

```text
transparent PNG/WebP
or
SVG-derived raster
```

with:

```text
alphaTest
```

where possible instead of fully blended transparent material.

This reduces sorting artifacts.

---

# 69. Logo geometry

Place signs a physically safe distance from facade:

```text
~0.03–0.10 m
```

depending on scale.

Do not put logo plane coplanar with facade.

---

# 70. Sign rendering quality

Use mipmaps/anisotropy where useful so text/logos remain legible without shimmering.

Large signs can remain visible in persistent IDENTITY layer.

---

# 71. Signage audit

Produce:

```text
total building-name signs

total corporate names

total verified logo graphics

total text-only fallbacks

total storefront signs

unverified/deferred signs
```

---

# PART VII — PUBLIC ART

# 72. Phase M23R-G — Finish ArtLayer

Current packages already have `art[]`.

Implement actual runtime rendering.

---

# 73. Official BGC arts directory

Use BGC's current Arts & Culture Directory as primary current-status evidence.

At review time it lists 19 works across locations including High Street portals, Terra 28th, Track 30th, De Jesus Oval, The Mind Museum and other BGC streets.

Snapshot it during implementation.

---

# 74. Art types

Support:

```text
SCULPTURE

INSTALLATION

MURAL

ART_MARKER
```

---

# 75. Sculptures

Where sufficient evidence and rights permit:

use simplified low-mid fidelity geometry.

---

# 76. Murals

Do not reproduce copyrighted artwork unless licensing permits it.

Use:

```text
correct wall

correct approximate dimensions

art-presence/color placeholder

artist/title metadata
```

when actual texture cannot be used.

---

# 77. Art graphics preset behavior

Art anchors should not disappear entirely in Performance.

Possible:

```text
Performance:
major art only

Balanced:
all important art

Quality:
all art + richer geometry/material
```

---

# PART VIII — COMPLETE ORIGINAL M23 GAPS

# 78. Phase M23R-H — Finish outstanding landmark work

Explicitly complete the outstanding items from the M23 report.

---

# 79. Shangri-La / One Bonifacio

Finish:

```text
glass bridges

arrival/drop-off arrangement

plaza relationships

ramped passage

major landscaping

shared urban courts
```

Use the existing Handel references from the original M23 chat.

---

# 80. Remaining approximate facades

For every M23 landmark:

review fixed cameras:

```text
front

rear

left

right

oblique

roof where relevant
```

Mark coverage:

```text
GOOD

PARTIAL

WEAK

NONE
```

Targeted research only for important `NONE`.

---

# PART IX — NEW EXPLORE CAMERA CONTROLS

# 81. Phase M23R-I — Replace MapControls with ExploreControls

The requested behavior is different from MapControls.

Implement a custom:

```text
ExploreControls
```

for `INSPECT`.

Do not modify Walk PointerLockControls.

---

# 82. Required controls

Exact required behavior:

```text
RIGHT CLICK + MOUSE MOVE
→ look around

camera position DOES NOT move

only yaw/pitch changes
```

```text
RIGHT CLICK HELD + W
→ move forward
```

```text
RIGHT CLICK HELD + S
→ move backward
```

```text
RIGHT CLICK HELD + A
→ move left
```

```text
RIGHT CLICK HELD + D
→ move right
```

```text
LEFT CLICK + DRAG
→ pan / slide camera

camera orientation remains unchanged
```

```text
SCROLL
→ zoom in/out
```

---

# 83. Right-look behavior

Do NOT use orbit behavior.

Right drag should rotate camera around:

```text
its own position
```

not around a target.

---

# 84. Right-look implementation

Track:

```text
yaw

pitch
```

Use mouse movement:

```text
movementX

movementY
```

or pointer deltas.

Clamp pitch approximately to avoid upside-down camera.

For example:

```text
-85° to +85°
```

Tune after testing.

---

# 85. Pointer capture

On right pointer down:

```text
canvas.setPointerCapture(pointerId)
```

where supported.

Release on:

```text
pointerup

pointercancel

window blur
```

---

# 86. Context menu

Prevent browser right-click menu:

```text
Canvas only
```

Do not disable browser context menus across the whole page.

---

# 87. WASD movement

WASD works only while:

```text
right mouse is held
```

as requested.

Otherwise normal keyboard interaction remains unaffected.

---

# 88. Movement plane

Use camera yaw to compute:

```text
horizontal forward

horizontal right
```

WASD should normally maintain current camera altitude.

Do not cause looking downward + W to crash camera into the ground.

---

# 89. Movement speed

Use delta-time movement.

Initial candidate:

```text
10–25 m/s
```

depending on current altitude.

Prefer altitude-sensitive speed:

```text
low altitude
→ slower

high aerial camera
→ faster
```

Keep deterministic bounds.

---

# 90. Boundary control

Keep camera inside padded project/navigation bounds.

Do not let user fly kilometers outside BGC.

---

# 91. Minimum altitude

Explore camera must not go underground.

Use:

```text
GroundSampler / base ground
+
minimum clearance
```

where applicable.

---

# 92. Maximum altitude

Set a reasonable limit for Explore.

Do not allow uncontrolled far-space flight.

Example target:

```text
~2–3 km
```

subject to actual experience.

---

# 93. Left-drag pan

Left dragging translates camera.

It must not rotate camera.

Use:

```text
camera-right vector

horizontal forward vector
```

to convert screen drag into world translation.

---

# 94. Left pan and altitude

Normal left pan should preserve altitude.

---

# 95. Scroll zoom

Scroll should dolly camera along its current look direction.

This can adjust:

```text
x

y

z
```

but still enforce:

```text
ground clearance

navigation bounds
```

---

# 96. Streaming anchor without MapControls target

The current runtime expects a focus/streaming anchor.

Because Explore no longer has an orbit target:

derive a streaming target from the camera.

Suggested:

```text
camera forward ray
↓
intersection with ground / detail terrain
```

Clamp look-ahead distance.

Suggested maximum:

```text
~300–600 m
```

If ray does not hit ground:

use:

```text
camera ground projection
+
horizontal look-ahead
```

---

# 97. Search focus

During Search transition:

```text
temporarily suspend manual Explore input
```

Camera transition sets:

```text
position

orientation
```

When complete:

resume ExploreControls.

---

# 98. Cancel behavior

If user begins:

```text
left drag

right drag

right+WASD

wheel
```

during an automatic Search focus transition:

cancel that transaction cleanly.

Do not restart it after rerender.

---

# 99. Tour

Tour remains automated.

ExploreControls must not mount in `TOUR`.

---

# 100. Walk

Walk remains PointerLock-based.

Do not merge Explore free-look with Walk controls.

---

# 101. Text-input safety

WASD must not move camera while user is typing in:

```text
Search

input

textarea

contenteditable
```

---

# 102. Input cleanup

Clear all input state on:

```text
pointerup

pointercancel

window blur

mode change

panel/input focus where required
```

Prevent stuck movement.

---

# 103. Help instructions

Update the normal Help section.

Add:

## Explore controls

```text
Left drag — Pan

Right drag — Look around

Hold Right Mouse + WASD — Fly

Scroll — Zoom
```

Optionally add:

```text
Search — Jump to a place
```

Do not use technical wording such as:

```text
orbit
dolly
yaw
```

in user-facing Help.

---

# PART X — SIMPLE GRAPHICS SETTINGS

# 104. Phase M24 — Graphics Settings

Only implement after the visual layers above are structurally working.

The UI should remain simple.

---

# 105. Public presets

Expose only:

```text
Performance

Balanced

Quality
```

Mark:

```text
Balanced — Recommended
```

Do not expose:

```text
LEGACY

LOW

FULL

detail=m23

tile mode

benchmark settings
```

to ordinary users.

Those remain debug-only.

---

# 106. Graphics Settings UI

Add a:

```text
Graphics
```

button/icon to the normal viewer shell.

Panel example:

```text
Graphics

○ Performance

● Balanced
  Recommended

○ Quality
```

Keep the panel compact.

---

# 107. Performance preset

Target:

```text
persistent designed facades:
ON

landmark identity:
ON

major building/company signs:
ON

shadows:
OFF

DPR:
~1

microdetail:
LOW

street furniture:
REDUCED

procedural vegetation:
REDUCED

minor art:
REDUCED

water animation:
OFF

near facade microdetail:
REDUCED
```

Important:

```text
building visual identity must NEVER revert
to blank generic boxes
```

even in Performance.

---

# 108. Balanced preset

Recommended default.

Target:

```text
persistent designed facades:
ON

landmark identity:
ON

full verified building/sign identity:
ON

public realm:
FULL

road detail:
FULL NORMAL

vegetation:
FULL NORMAL

art:
ON

microdetail:
MEDIUM

shadows:
OFF or measured selective implementation

DPR:
1–1.5

water:
STATIC or light animation
```

---

# 109. Quality preset

Target:

```text
persistent designed facades:
ON

landmark identity:
ON

near facade detail:
FULL

signs/logos:
FULL

public art:
FULL

streetscape:
FULL

vegetation:
FULL

microdetail:
FULL

water animation:
ON

shadows:
ON / SELECTIVE

DPR:
~1.25–2
```

Exact settings must be benchmark-driven.

---

# 110. Do not change design identity by preset

Graphics presets may change:

```text
small-object density

shadows

render resolution

microdetail

animations
```

They must NOT fundamentally change:

```text
building silhouette

facade identity

major materials

major signage

major terrain
```

---

# 111. GraphicsConfig

Introduce a single resolved configuration.

Conceptually:

```text
GraphicsConfig {
  profile

  dprMin
  dprMax

  shadows

  persistentFacade
  landmarkIdentity

  nearFacadeDetail
  microDetail

  publicRealm
  roadDetail

  vegetationDensity

  signageLevel
  artLevel

  waterAnimation
}
```

---

# 112. Remove Canvas remount on quality change

Current Canvas is keyed by environment quality.

Refactor so changing Graphics settings does NOT unnecessarily destroy and recreate the entire 3D viewer.

Changing Graphics must not:

```text
reset camera

lose selection

reload world

restart Search state
```

---

# 113. Persist preference

Store:

```text
bgc.graphics.v1
```

in `localStorage`.

---

# 114. URL override

For QA/debug:

support:

```text
?graphics=performance

?graphics=balanced

?graphics=quality
```

URL takes precedence over stored preference for that page.

---

# 115. Debug controls

Keep existing diagnostic controls behind:

```text
?debug=1
```

Debug can override internal components separately.

---

# 116. Accessibility

Graphics panel:

```text
keyboard accessible

focus trapped/restored appropriately

Esc closes

radio-group semantics

clear selected state
```

---

# PART XI — VISUAL COVERAGE VALIDATION

# 117. Building-design coverage

Generate a report:

```text
canonical buildings

building volumes

facade-designed buildings

facade fallback buildings

plain buildings

named buildings

bespoke buildings
```

Target:

```text
plain valid buildings = 0
```

---

# 118. Persistent identity validation

For all M23 landmarks:

test at multiple ranges:

```text
near

250 m

500 m

1 km

aerial
```

Verify:

```text
identity remains recognizable
```

Microdetail may disappear.

---

# 119. High Street coverage report

Report:

```text
hero area m²

designed ground area m²

unknown/uncovered area m²

coverage %

largest uncovered region
```

---

# 120. Road coverage

Report:

```text
roads with width

roads with lanes

roads with markings

bike lanes

crosswalks

signals

curb-detail zones

bus stops
```

---

# 121. Signage coverage

Report:

```text
building-name anchors

company-name anchors

graphic logos

text-only fallbacks

storefront signs

major persistent signs

near-only signs

deferred/unverified signs
```

---

# 122. Art coverage

Report:

```text
official works discovered

located

rendered as geometry

rendered as texture

placeholder

deferred
```

---

# PART XII — PERFORMANCE

# 123. Re-run performance after ALL final changes

The previous matched benchmark predates the latest terrain-prop exclusion fix.

Therefore it is not the final acceptance benchmark.

Run again after:

```text
facade fixes

persistent identity

universal facades

road/environment additions

signage/logos

art

Explore controls

graphics profiles
```

---

# 124. Valid benchmark requirements

Require:

```text
foreground browser

correct viewport

correct DPR

no ~1 FPS throttling

same camera path

same duration

movement stops when sample stops
```

---

# 125. Benchmark each preset

Run:

```text
Performance

Balanced

Quality
```

for:

```text
Explore High Street

Explore Uptown / dense towers

Walk High Street

Walk High Street Central

Tour
```

---

# 126. Performance priority

Optimize in this order:

```text
draw calls

large always-loaded geometry

texture memory

active microdetail

instance counts

shadow cost
```

Do not remove persistent building identity merely to improve FPS.

---

# 127. Facade optimization

Far facades should primarily use:

```text
shared atlas/material
```

rather than thousands of individual panels.

Near geometry can provide:

```text
real fins

balconies

screens
```

---

# 128. Sign optimization

Atlas or cache generated text/logo textures.

Do not create duplicate CanvasTextures for identical logos/text.

---

# PART XIII — MANUAL USER VALIDATION

# 129. Required visual tests

User should manually inspect:

## Flicker

```text
slow orbit/look around tall buildings

fast pan

scroll zoom

Search transition

aerial view
```

Expected:

```text
no shimmering facade layers
```

---

## Distance fidelity

Move away from:

```text
PSE

ACPT

SM Aura

Mitsukoshi

Mind Museum

Shangri-La
```

Expected:

```text
architecture simplifies gradually

but recognizable identity remains
```

---

## Generic buildings

Travel through ordinary office/residential blocks.

Expected:

```text
every building has intentional facade pattern

no city of plain solid-color blocks
```

---

## High Street

Expected:

```text
continuous intentional ground treatment

paving

landscape

street furniture

roads

ramps/stairs

retail fronts
```

---

## Roads

Expected:

```text
lane structure

crossings

bike infrastructure

curbs/signage

street furniture
```

where supported.

---

## Logos/names

Expected:

```text
major building names visible

verified company signs visible

current storefront identity where appropriate

no invented companies
```

---

## Explore camera

Expected:

```text
Right drag:
look only

Right + WASD:
fly

Left drag:
pan

Scroll:
zoom
```

---

## Graphics

Switch:

```text
Performance
Balanced
Quality
```

Expected:

```text
camera position preserved

no world reload

visual quality visibly changes

building identity remains
```

---

# PART XIV — AUTOMATED REGRESSION

# 130. Existing runtime gates

Require:

```text
zero visible-world blank events

zero unexplained repeated tile requests

zero LOD handoff gaps

Search transitions PASS

Tour transitions PASS

Walk PASS

street locator PASS
```

---

# 131. New Explore-control tests

Automated tests should cover:

```text
right drag changes quaternion
but not position

right-held W moves forward

right-held S moves backward

right-held A/D strafes

W without right mouse does not move

left drag moves position
but not orientation

wheel changes position along look direction

text input blocks movement

blur clears keys
```

---

# 132. Graphics tests

Require:

```text
preset persistence

URL override

no Canvas/camera reset

profile config resolution

Performance/Balanced/Quality layer mapping
```

---

# 133. Flicker structural tests

Require:

```text
duplicate facade surfaces = 0

unintended coplanar surfaces = 0

invalid sign/facade overlap = 0
```

---

# 134. Determinism

Rebuild twice.

Require stable hashes for unchanged generated assets.

---

# PART XV — IMPLEMENTATION ORDER

Execute strictly in this order:

```text
1. Audit current M23 output

2. Add facade overlap/depth diagnostics

3. Fix facade flicker structurally

4. Refactor persistent identity vs near detail

5. Stop global M23 geometry rebuild churn

6. Build universal all-building facade system

7. Make 31 landmark identities persistent

8. Complete High Street ground coverage

9. Expand roads / curbs / bike / crossing detail

10. Expand environment detail

11. Upgrade signage schema

12. Add company/building/store names

13. Add verified logo assets

14. Implement ArtLayer

15. Finish Shangri-La / One Bonifacio gaps

16. Finish remaining landmark QA

17. Implement new ExploreControls

18. Update Help instructions

19. Implement Graphics Settings

20. Run final deterministic validation

21. Run final valid performance benchmarks

22. Generate reports

23. STOP for user visual validation
```

Do not skip to Graphics Settings before visual layers are structurally stable.

---

# PART XVI — REQUIRED REPORTS

Update/create:

```text
docs/visual/M23R_RENDER_STABILITY.md

docs/visual/M23R_BUILDING_FIDELITY.md

docs/visual/M23R_HIGH_STREET_COMPLETION.md

docs/visual/M23R_ROAD_ENVIRONMENT.md

docs/visual/M23R_SIGNAGE_ART.md

docs/visual/M23R_VISUAL_ACCEPTANCE.md

docs/M24_GRAPHICS_NAVIGATION.md
```

Machine reports:

```text
data/reports/m23r-facade-stability.json

data/reports/m23r-building-coverage.json

data/reports/m23r-public-realm.json

data/reports/m23r-road-detail.json

data/reports/m23r-signage.json

data/reports/m23r-art.json

data/reports/m23r-performance.json

data/reports/m24-navigation-graphics.json
```

Avoid redundant reports if existing report structure can be extended cleanly.

---

# PART XVII — ACCEPTANCE GATES

## Facades

PASS requires:

```text
flicker structurally resolved

no known coplanar facade defect

persistent landmark identity works

all valid buildings have facade design
```

---

## Public realm

PASS requires:

```text
High Street ground substantially complete

High Street Central remains terrain-aware

major parks remain distinct

roads visibly improved

bike/crossing/curb systems represented
```

---

## Signage

PASS requires:

```text
major building names present

verified company/store signs supported

logo asset provenance recorded

no invented business identity
```

---

## Art

PASS requires:

```text
ArtLayer implemented

official anchors accounted for

rights restrictions respected
```

---

## Explore Controls

PASS requires:

```text
right drag = fixed-position look

right + WASD = fly

left drag = pan

scroll = zoom
```

Manual feel:

```text
AWAITING_USER_TEST
```

---

## Graphics

PASS requires:

```text
Performance

Balanced

Quality
```

available through simple public UI.

Changing preset must not reset the camera/world.

---

# PART XVIII — REQUIRED FINAL CODEX RESPONSE

Return:

```text
Phase:
READY_FOR_USER_VALIDATION / PARTIAL / FAIL

Milestone:
M23R–M24 — Visual Fidelity Completion, Explore Controls & Graphics Settings


Repository:

Branch:
<value>

Starting HEAD:
<sha>

Final HEAD:
<sha>

Working tree:
CLEAN / DIRTY


Facade stability:

Exact duplicate surfaces:
<count>

Coplanar violations:
<count>

Near-coplanar warnings:
<count>

Double-sided opaque facade materials remaining:
<count>

Reverse depth:
ENABLED / UNSUPPORTED / NOT_NEEDED

Explore near/far:
<values>


Building coverage:

Canonical buildings:
<count>

Buildings with facade design:
<count>

Plain valid buildings:
<count>

Procedural designed:
<count>

Evidence-specific:
<count>

Persistent landmark identities:
<count>


Distance fidelity:

Landmarks tested:
<count>

Identity lost at distance:
<count>

Microdetail culled correctly:
PASS / FAIL


High Street:

Hero ground coverage:
<percent>

Unknown/uncovered ground:
<area>

Paving:
PASS / PARTIAL

Landscape:
PASS / PARTIAL

Furniture:
PASS / PARTIAL

Stairs/ramps:
PASS / PARTIAL

Water:
PASS / PARTIAL


Roads:

Roads analyzed:
<count>

Roads with visual markings:
<count>

Crosswalks:
<count>

Bike-lane segments:
<count>

Signals:
<count>

Curbs/detail zones:
<count>

Bus stops:
<count>


Signage:

Building-name signs:
<count>

Corporate/company names:
<count>

Graphic logos:
<count>

Text-only fallbacks:
<count>

Storefront signs:
<count>

Deferred/unverified:
<count>


Art:

Official art records:
<count>

Rendered geometry:
<count>

Rendered licensed textures:
<count>

Placeholders:
<count>

Deferred:
<count>


Explore controls:

Right-drag fixed-position look:
PASS / FAIL

Right+WASD:
PASS / FAIL

Left pan:
PASS / FAIL

Scroll zoom:
PASS / FAIL

Text-input safety:
PASS / FAIL

Boundary/ground safety:
PASS / FAIL


Help:

Explore instructions:
PASS / FAIL


Graphics Settings:

Performance:
PASS / FAIL

Balanced:
PASS / FAIL

Quality:
PASS / FAIL

Preference persistence:
PASS / FAIL

URL override:
PASS / FAIL

Camera preserved while switching:
PASS / FAIL


Runtime:

Zero-visible events:
<count>

Repeated requests:
<count>

LOD gaps:
<count>

Runtime errors:
<count>


Performance:

Performance profile:
<metrics>

Balanced profile:
<metrics>

Quality profile:
<metrics>

Invalid throttled runs:
<count>


Engineering:

Build:
PASS / FAIL

Lint:
PASS / FAIL

Product:
PASS / FAIL

Python tests:
<count PASS>

Determinism:
PASS / FAIL

Metadata:
PASS / FAIL


Automated implementation:
PASS / PARTIAL / FAIL


Manual validation:

Facade flicker:
AWAITING_USER_TEST

Distance fidelity:
AWAITING_USER_TEST

Generic-building improvement:
AWAITING_USER_TEST

High Street environment:
AWAITING_USER_TEST

Road realism:
AWAITING_USER_TEST

Logo/sign accuracy:
AWAITING_USER_TEST

Explore camera feel:
AWAITING_USER_TEST

Graphics visual difference:
AWAITING_USER_TEST


M23R:
READY_FOR_USER_VALIDATION / PARTIAL / FAIL

M24:
READY_FOR_USER_VALIDATION / PARTIAL / FAIL


Do NOT begin another milestone automatically.
```

---

# Final rule

The visual system should now follow this hierarchy:

```text
EVERY BUILDING
gets intentional facade design

↓

IMPORTANT BUILDINGS
get persistent recognizable identity

↓

NEARBY IMPORTANT BUILDINGS
gain finer architecture

↓

HERO ZONES
gain terrain, landscape, streetscape,
signage and art

↓

GRAPHICS SETTINGS
change expensive detail

NOT core identity
```

The user should never again experience:

```text
beautiful building
↓
move away
↓
plain box
```

The correct behavior is:

```text
high-detail building
↓
move away
↓
simplified but still recognizable building
```

And the Explore camera must behave exactly as:

```text
Right drag
→ Look around

Right mouse + WASD
→ Fly

Left drag
→ Pan

Scroll
→ Zoom
```

These instructions must also appear in the public Help section.