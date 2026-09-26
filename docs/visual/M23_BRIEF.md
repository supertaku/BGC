# M23 — Comprehensive BGC Heavy Visual Refinement

## Mission

Transform the current BGC 3D environment from a geographically correct low-fidelity city into a **recognizably Bonifacio Global City low-to-mid fidelity environment**.

The target is not photorealism.

The target is:

```text
correct urban identity
+
correct public-realm hierarchy
+
recognizable landmarks
+
recognizable parks
+
credible streets
+
credible terrain where important
+
credible landscaping
+
selective signage and art
+
good runtime performance
```

A user walking around the model should be able to recognize major parts of BGC without depending primarily on labels.

Graphics Settings are explicitly postponed until this milestone is substantially complete.

---

# A. Operating instructions

## A1. Inspect repository first

Before changing anything:

- inspect actual `main`
- inspect current HEAD
- inspect git status
- inspect generated assets
- inspect existing M19/M20/M21/M22 reports
- inspect current public-realm packages
- inspect existing LOD1 registry
- inspect current performance/runtime systems

Do not reset legitimate newer work.

At plan preparation time, the last verified heavy-refinement foundation was based on the M21R–M22R work after:

```text
039ebda66e3a3294a57d96db686b037c8e30e27f
```

but the actual repository is authoritative.

---

## A2. Preserve existing runtime architecture

Do not break:

- dynamic tile streaming
- last-good-visible-set logic
- per-tile Suspense isolation
- per-landmark Suspense isolation
- Search
- Tour
- Walk
- street names
- MapControls
- PointerLock
- tile/LOD readiness
- current seven approved LOD1 assets
- M21/M22 lazy-loaded public realm
- provenance tracking
- exclusion/dedup logic
- LOW environment default

This milestone extends visual content.

It does not redesign the viewer unless a new requirement genuinely requires it.

---

# B. Research policy

## B1. Use this brief as the primary research pack

Do NOT begin M23 with broad internet research.

The reference pages and visual descriptions supplied with this plan already define the main visual targets.

Codex should spend most effort on:

```text
model
generate
render
compare
refine
validate
```

rather than:

```text
search
search
search
```

---

## B2. Targeted research is allowed only when necessary

New research may be performed only when:

- a critical facade side has no reference
- exact terrain relationship is unclear
- current signage may have changed
- a building identity is ambiguous
- an artwork's current status is uncertain
- geometry sources conflict
- rights status is unclear
- an important detail cannot be implemented conservatively

Research only the missing item.

Prefer:

1. official owner/developer
2. official architect
3. BGC official sources
4. Wikimedia Commons
5. other strong reference photography

Stop once enough evidence exists for low-to-mid fidelity.

---

# C. Evidence system

Every modeled visual feature must have a grounding state:

```text
VERIFIED_GEOGRAPHIC
VERIFIED_VISUAL
INFERRED
ESTIMATED
PROCEDURAL
UNKNOWN
CONFLICTED
```

Do not silently turn assumptions into facts.

Every important visual-detail record should know:

```text
feature_id
zone_id
source_ids
grounding
confidence
modeling_notes
rights_status
```

---

# D. Reference database

Create:

```text
data/visual_reference/
```

Recommended structure:

```text
data/visual_reference/
  manifest.json

  zones/
    bgc_citywide.json
    high_street.json
    high_street_central.json
    track_30th.json
    terra_28th.json
    kasalikasan.json
    greenway.json
    burgos_circle.json
    one_bonifacio.json
    mind_museum.json
    sm_aura.json
    uptown.json
    mitsukoshi.json
```

Do not store copyrighted research images unless reuse permits it.

For research-only images, store the source page and observations instead.

---

## D1. Reference entry schema

Each source should record approximately:

```json
{
  "source_id": "",
  "entity_id": "",
  "zone": "",
  "title": "",
  "source_type": "OFFICIAL_ARCHITECT",
  "source_domain": "",
  "viewpoint": "",
  "use_for": [],
  "do_not_infer": [],
  "confidence": "HIGH",
  "rights_status": "RESEARCH_ONLY"
}
```

---

# E. Visual QA workflow

For every important zone or landmark:

```text
reference evidence
↓
initial procedural/Blender build
↓
fixed-camera render
↓
visual comparison
↓
discrepancy record
↓
deterministic patch
↓
render again
```

If Astra is available, use Astra for visual comparison.

Astra decides:

```text
WHAT looks wrong
```

Sol/scripts implement:

```text
HOW it is corrected
```

Do not rely on non-reproducible manual Blender edits.

---

# F. Fidelity hierarchy

## F1. LOD2 — background BGC

Keep current general BGC representation:

- real footprint
- height
- basic type/material
- roads
- basic paths
- sparse environmental objects

Most of the city stays here.

---

## F2. LOD1-Lite — new intermediate layer

Introduce a reusable intermediate landmark/detail class.

LOD1-Lite should provide:

- correct silhouette
- podium/tower distinction
- major facade rhythm
- important fins/bands
- balcony rhythm where relevant
- dominant materials
- entrance/canopy
- roof silhouette
- primary building-name signage

Do NOT model:

- every window
- every mullion
- interior rooms
- invisible MEP
- minor ornament

Candidate final quantity should be based on evidence and performance, likely tens rather than hundreds.

---

## F3. LOD1 — priority landmarks

Use more building-specific geometry.

Existing approved seven remain valid.

---

## F4. Hero zones

Highest effort:

- High Street
- High Street Central
- One Bonifacio/PSE/Shangri-La/Suites
- Mind Museum
- SM Aura
- possibly Mitsukoshi

Hero zones include both buildings and public realm.

---

# G. Citywide BGC visual grammar

BGC should not resemble a generic US downtown.

The district identity includes:

- broad pedestrian sidewalks
- landscaped streets
- modern commercial/residential towers
- strong ground-floor retail
- plazas
- parks
- public art
- bike infrastructure
- trees
- covered/arcaded walking edges
- integrated mixed-use podiums

Implement a reusable BGC city kit.

---

# H. Road system

Create reusable road-detail types:

```text
ROAD_MAIN
ROAD_SECONDARY
ROAD_SERVICE
ROAD_DROP_OFF
ROAD_PARKING_EDGE
```

Support:

- asphalt variation
- lane lines
- center lines
- directional arrows
- turn arrows
- stop lines
- zebra crossings
- bike-lane markings
- curbside parking markings
- service/loading markings
- median geometry where verified

Use OSM/current visual sources for location.

Do not uniformly add lane markings everywhere.

---

# I. Bike infrastructure

BGC officially has dedicated bike lanes and racks.

Support:

```text
BIKE_LANE_PAINTED
BIKE_LANE_PROTECTED
BIKE_BOLLARD
BIKE_RACK
```

Use local evidence per road.

Do not assume all lanes use one treatment.

---

# J. Curbs and drainage

Add a reusable low-cost curb kit:

```text
CURB_STANDARD
CURB_DROP
CURB_RAMP
CURB_ISLAND
GUTTER
DRAIN_GRATE
STORM_INLET
```

This detail is visually important in Walk mode.

Keep geometry simple.

---

# K. Traffic infrastructure

Create reusable:

```text
TRAFFIC_SIGNAL
PEDESTRIAN_SIGNAL
STREET_NAME_SIGN
DIRECTION_SIGN
PARKING_SIGN
BOLLARD
ROAD_BARRIER
LANE_SEPARATOR
```

Exact placement should follow mapped or visually verified locations where practical.

---

# L. Urban utility detail

Use sparingly:

```text
MANHOLE
UTILITY_COVER
FIRE_HYDRANT
UTILITY_CABINET
CCTV_POLE
SECURITY_OBJECT
```

Do not clutter every street.

---

# M. BGC bus system

BGC has its own internal bus network.

Create:

```text
BGC_BUS_STOP_STANDARD
BGC_BUS_STOP_COMPACT
BGC_BUS_STOP_SIGN
```

Research exact visual shape only if necessary.

Prioritize:

- shelter
- bench
- route/information panel
- BGC identity
- queue area

Bus vehicles may remain a future optional asset.

---

# N. Arcades, awnings and covered walks

These are important for BGC street-level identity.

Create reusable:

```text
ARCADE_SIMPLE
ARCADE_COLUMN
CANOPY_GLASS
CANOPY_METAL
AWNING_RETAIL
COVERED_WALK
SKYWALK_SIMPLE
```

Use only where building references support them.

---

# O. Tree system

Do not use one generic tree everywhere.

Create low-poly archetypes:

```text
TREE_SMALL_ROUND
TREE_MEDIUM_ROUND
TREE_LARGE_SPREAD
TREE_COLUMNAR
TREE_FLOWERING
PALM_ROYAL
TREE_MULTI_TRUNK
```

Historic BGC planting guidance references species including:

- Narra
- Bauhinia
- Jacaranda
- Royal Palm
- Eucalyptus
- Melaleuca
- Grevillea
- Brachychiton

Do NOT treat this as proof that every current BGC tree is one of those species.

Use these only to guide visual variety.

Mapped trees remain higher-authority than generated trees.

---

# P. Landscape kit

Create instanced:

```text
LAWN_SHORT
LAWN_CARABAO
SHRUB_LOW
SHRUB_DENSE
TROPICAL_FOLIAGE
FLOWERING_SHRUB
PALM_CLUSTER
ORNAMENTAL_GRASS
GROUNDCOVER
```

Reuse materials.

Do not create thousands of unique meshes.

---

# Q. High Street — hero public realm

High Street should be the most recognizable pedestrian environment.

Key identity:

```text
landscaped central spine
+
low-rise retail edges
+
wide pedestrian paving
+
shade trees
+
awnings/canopies
+
planters
+
benches
+
public art
+
water features
+
outdoor dining
```

It should NOT resemble an ordinary roadway.

---

# R. High Street paving

Replace generic visual border logic with proper surface categories:

```text
HIGH_STREET_MAIN_PAVER
HIGH_STREET_EDGE_PAVER
HIGH_STREET_PLAZA
HIGH_STREET_SERVICE
```

Use simple procedural or repeating material logic.

Priority is visible paving rhythm, not high-resolution texture detail.

---

# S. High Street vegetation

Model:

- continuous tree rhythm
- planted beds
- lawns
- shrub masses
- palm accents where verified
- planter islands

Existing verified trees remain authoritative.

---

# T. High Street furniture

Develop High Street-specific:

```text
BHS_BENCH
BHS_PLANTER
BHS_LIGHT
BHS_BIN
BHS_BOLLARD
BHS_BIKE_RACK
```

Do not reuse one generic object family across the whole city.

---

# U. High Street storefronts

Ground floors deserve more detail than upper stories.

Support:

```text
SHOPFRONT_GLASS
SHOP_ENTRY
SHOP_FRAME
SIGN_BAND
CANOPY
AWNING
```

Use simple dark backing planes behind storefront glass.

Do not model interiors.

---

# V. Outdoor dining

Where visually evident:

- tables
- chairs
- umbrellas
- planter separators
- queue barriers

Use instancing and zone rules.

Do not populate every storefront.

---

# W. High Street Central — terrain hero zone

Primary source:

```text
Crearis — Bonifacio High Street Central
```

Confirmed elements:

- amphitheater
- interactive water feature
- plaza
- feature gardens
- native/sustainable planting intent

This zone should no longer remain flat.

---

# X. High Street Central local terrain

Create a dedicated terrain/detail mesh.

Support:

```text
upper terrace
lower plaza
ramps
steps
retaining/planter edges
amphitheater transition
```

Do NOT deform whole BGC.

This is a localized detail zone.

---

# Y. GroundSampler

Update Walk to support local vertical surfaces.

Create:

```text
GroundSampler
```

Ground resolution order:

```text
detail terrain
>
local terrain patch
>
base BGC ground
```

Walk camera:

```text
camera_y = sampled_ground_y + eye_height
```

Keep current flat behavior outside detail zones.

---

# Z. Stairs

Create reusable:

```text
STAIR_PLAZA_WIDE
STAIR_LANDSCAPE
STAIR_ENTRY
```

Only place where visually supported.

For Walk collision:

use a hidden smoothed ramp if required.

This prevents camera jitter.

---

# AA. Ramps and slopes

Create:

```text
RAMP_ACCESSIBLE
RAMP_PLAZA
SLOPE_LANDSCAPE
```

Use relative visual evidence.

Do not claim surveyed gradients.

---

# AB. Amphitheater

Model:

- primary bowl/descent
- seating/terrace rhythm
- central plaza/stage relationship
- retaining edges
- landscape integration
- railings if visible

The silhouette and level relationship matter more than every step.

---

# AC. High Street Central water

Represent using:

```text
WATER_PLAZA
FOUNTAIN_NOZZLE
OPTIONAL_JET
```

Use:

- reflective/simple water plane
- dark wet-surface material if appropriate
- simple optional animated jets

No fluid simulation.

---

# AD. Track 30th

Officially characterized by BGC as:

- jogging paths
- yoga lawns
- meditation gardens
- outdoor art
- bicycle/PMD parking

Build a distinct fitness-park visual language.

Create:

```text
RUNNING_PATH
FITNESS_LAWN
MEDITATION_GARDEN
BIKE_PARKING
OUTDOOR_ART_ANCHOR
```

Do not copy High Street design.

---

# AE. Terra 28th

Target identity:

- shaded family park
- grass
- trees
- informal circulation
- play-oriented spaces
- public art
- colorful urban objects

Use current BGC Arts references for art locations.

---

# AF. Kasalikasan

Official BGC Arts reference confirms:

- 3,556 m² living sculpture
- mandala
- meditation/prayer area
- elevated circular stage
- carabao grass
- sandbox
- pebbled pathways

This has enough geometric identity for a dedicated reconstruction.

Build:

```text
raised circular stage
mandala/open center
grass
pebble paths
sandbox
dense planting
```

---

# AG. De Jesus Oval

Use:

- mature trees
- oval circulation
- denser canopy
- pedestrian path
- Kasalikasan relationship

Avoid generic sparse tree distribution.

---

# AH. Greenway

Give the Greenway a distinct linear-park identity:

- walking/jogging route
- continuous shade
- vegetation corridor
- occasional seating
- lower urban density feeling

Do not make it another plaza.

---

# AI. Burgos Circle / Forbes Town

Distinct character:

- circular central park
- residential towers
- tree-lined sidewalk
- cafe frontage
- alfresco dining
- mixed ground-floor retail

Develop:

```text
BURGOS_CIRCLE_PARK
FORBES_CAFE_EDGE
FORBES_RETAIL_FRONT
```

Use current imagery before exact furniture placement.

---

# AJ. PSE / Suites / Shangri-La / One Bonifacio

Model as ONE urban ensemble.

Do not reconstruct them independently and ignore their shared public realm.

Relationships matter:

```text
Shangri-La
        |
elevated plaza
        |
PSE --- courts --- Suites
        |
One Bonifacio retail
        |
High Street
```

---

# AK. Philippine Stock Exchange Tower

Primary reference:

```text
Handel Architects — Philippine Stock Exchange
```

Defining cues:

- inflected glass frontpiece
- expressed spine
- deep vertical ribs
- high transparency
- shared multilevel urban plaza
- commercial podium relationship

Do not replace this with generic facade bands.

---

# AL. PSE street-level identity

Where visually confirmed, also consider:

- drop-off canopy
- large glass lobby
- PSE signage
- ticker/LED identity element
- podium interface

Keep signage separately configurable.

---

# AM. The Suites

Primary reference:

```text
Handel Architects — The Suites at One Bonifacio High Street
```

Defining cues:

- luxury residential glass/masonry tower
- curved/softened overall mass where visible
- horizontal facade expression
- balcony rhythm
- relationship with landscaped public spaces
- connection to One Bonifacio

Use current visual references for exact facade treatment.

---

# AN. Shangri-La at the Fort

Primary reference:

```text
Handel Architects — Shangri-La at the Fort
```

Confirmed defining cues:

- 61-storey tower
- two long and two short sliding facade volumes
- stepped appearance at oblique angles
- curtainwall
- east/west louvers
- Tunisian limestone and dark granite podium
- elevated hotel drop-off
- fountain-centered arrival
- elevated urban plaza
- open-air ramped passageway
- three glass bridges
- landscaped amenity terrace

These are extremely important identity cues.

---

# AO. One Bonifacio retail podium

Prioritize:

- podium proportions
- glazing
- major entrances
- escalator/vertical circulation expression if externally visible
- restaurant/retail frontage
- High Street termination
- plaza relationship

Do not model mall interiors.

---

# AP. ArthaLand Century Pacific Tower

Primary:

```text
SOM — ArthaLand Century Pacific Tower
```

Confirmed:

- 136 m
- 32 stories
- overlapping glass facade
- facade appearance changes with height
- parking podium concealed by facade
- transparent full-height lobby glazing on three sides
- rooftop garden terrace

The current project may contain a conflicting height.

Do NOT silently replace it.

Record:

```text
HEIGHT_CONFLICT
```

and reconcile provenance.

---

# AQ. Central Square

Existing approved LOD1 remains.

Refine only where meaningful.

Priorities:

- primary horizontal bands
- large openings
- glazed storefronts
- entrances
- cinema/upper volume
- mall identity signage
- key anchor storefronts

Do NOT model every tenant.

---

# AR. UNIQLO High Street

Model:

- recognizable low-rise store volume
- large glazed storefront
- major UNIQLO sign
- current entrance organization

Use only official/appropriate brand assets.

Do not reproduce unrelated copyrighted BGC murals.

---

# AS. The Mind Museum

Primary reference:

```text
The Mind Museum — official site
```

High-value identity:

- broad sweeping curved roof
- asymmetric low-rise mass
- dark structural supports
- glazed portions
- landscaped forecourt
- JY Campos Park
- People's Minds artwork location

This should be a signature low-rise asset.

---

# AT. Mind Museum public realm

Model:

- curved approach paths
- planting beds
- shaded trees
- outdoor sculpture markers
- entrance plaza
- canopy/covered approach

Do not model museum interiors.

---

# AU. SM Aura Premier

Primary:

```text
SM Prime official SM Aura architecture sources
```

Defining cues:

- three curvilinear ribbon forms
- staggered northern openings
- ribbons turning vertically into office tower
- green terraces
- major roof landscape
- sculptural mall massing

This deserves hero-level treatment.

---

# AV. SM Aura Sky Park

Confirmed:

- fifth-level multi-level roof garden
- lawns
- landscape
- water features
- open-air performance spaces
- sculpture courts
- alfresco restaurants
- Chapel of San Pedro Calungsod
- Samsung Hall
- smaller egg-shaped skylights

Model visible external forms only.

---

# AW. SM Aura chapel

Create recognizable tubular/arched form.

Do not model interiors.

---

# AX. Samsung Hall

Use recognizable egg/dome form.

Maintain low polygon count.

---

# AY. Mitsukoshi BGC

Primary:

```text
Federal Land — Mitsukoshi BGC
```

Most important exterior cue:

```text
modernized Japanese hemp-leaf geometric facade pattern
```

Create an efficient repeating screen system rather than modeling each opening manually.

Also model:

- glazed base
- major entrances
- red identity accents where current references support them
- Mitsukoshi signage

---

# AZ. The Seasons Residences

Primary:

```text
Federal Land — The Seasons Residences
```

Current official source confirms:

- Japanese-influenced architecture
- traditional hemp-pattern facade
- four seasonal tower identity

Externally model:

- tower composition
- vertical facade rhythm
- hemp-pattern podium/screen relationship
- connection to Mitsukoshi

Do not model private amenity interiors.

---

# BA. Uptown district

The visual language differs from High Street.

Character:

- taller towers
- larger podiums
- glass/steel facades
- dense retail
- nightlife
- illuminated commercial frontage
- wide urban intersections

Build separate Uptown public-realm assumptions.

---

# BB. Uptown Mall

Primary:

```text
Megaworld — Uptown Mall
```

Confirmed:

- podium for multiple towers
- five retail levels including lower ground
- major integrated mixed-use mass

Model:

- mall podium
- large entrances
- retail glazing
- mall signage
- drop-off geometry
- tower connections

---

# BC. One Uptown Residence

Primary:

```text
Megaworld — One Uptown Residence
```

Confirmed:

- glass/aluminum facade
- water cascade
- multiple sky gardens
- ground-level retail
- green wall / landscaped amenity expression

Only externally visible features.

---

# BD. Uptown Parksuites

Confirmed:

- all-glass-and-steel facade
- 46/50-storey towers
- upper-level sky lounges
- podium amenities
- commercial ground strip

Use LOD1-Lite unless hero evidence justifies more.

---

# BE. Other Uptown towers

Select LOD1-Lite candidates based on:

- visual importance
- recognizable shape
- street visibility
- evidence availability

Do not hand-model every tower.

---

# BF. Serendra

Exterior refinement should emphasize:

- residential podium
- landscaped edge
- tree-heavy public realm
- ground-floor retail
- pedestrian connections

Private pools/amenities are not a priority.

---

# BG. Market! Market!

Use current reference imagery.

High-value external cues:

- major mall mass
- entrance
- identity sign
- transport edge
- loading/service edge
- pedestrian relationship with BGC

Do not model interiors.

---

# BH. McKinley Parkway

Use stronger:

- major road geometry
- signalized crossings
- trees
- bike/pedestrian infrastructure
- mall interfaces
- medians where verified

---

# BI. High Street South

Build stronger context around:

- One Maridien
- Verve
- W Global
- C1/C2/C3
- nearby parks and open spaces

Focus on:

- entrances
- balconies
- podiums
- retail
- sidewalks
- landscaping

---

# BJ. Office-grid buildings

Create reusable office facade families rather than leaving everything as blank blocks.

Families:

```text
OFFICE_GLASS_BLUE
OFFICE_GLASS_NEUTRAL
OFFICE_STONE_GLASS
OFFICE_VERTICAL_FIN
OFFICE_HORIZONTAL_BAND
OFFICE_METAL_PANEL
```

Derive choice from building tags/reference evidence.

---

# BK. Residential facade families

Create:

```text
RESIDENTIAL_BALCONY_GRID
RESIDENTIAL_GLASS_BALCONY
RESIDENTIAL_VERTICAL_WINDOW
RESIDENTIAL_PODIUM_TOWER
```

Do not randomly assign them.

Use building type and reference clues.

---

# BL. Facade-generator primitives

Implement reusable deterministic primitives:

```text
WINDOW_GRID
CURTAIN_WALL
HORIZONTAL_BAND
VERTICAL_FIN
LOUVER_SCREEN
BALCONY_STACK
STONE_PANEL
METAL_PANEL
PODIUM_GLAZING
CANOPY
ROOF_SCREEN
SKY_GARDEN_VOID
```

This becomes the foundation for LOD1-Lite.

---

# BM. Material library

Create controlled shared materials:

```text
GLASS_BLUE
GLASS_NEUTRAL
GLASS_DARK
GLASS_GREEN
ALUMINUM_LIGHT
ALUMINUM_DARK
STONE_LIGHT
STONE_BEIGE
STONE_DARK
CONCRETE_LIGHT
CONCRETE_DARK
BRICK_WARM
WOOD_WARM
METAL_BLACK
SOIL
GRASS
WATER
```

Reuse aggressively.

---

# BN. Glass rendering

Do not make every BGC building bright cyan.

Use restrained differences in:

- tint
- roughness
- opacity/reflectivity approximation

Avoid expensive refraction.

---

# BO. Facade depth

Important facade elements should have small geometric depth.

Examples:

- fins
- screens
- bands
- balcony slabs
- mullion groups

Do not keep every facade accent coplanar.

---

# BP. Roof silhouettes

Add where visually important:

```text
MECHANICAL_SCREEN
PARAPET
ROOF_GARDEN
CROWN
ANTENNA
```

Aerial silhouette is important.

---

# BQ. Entrances

Where visible:

- recess
- canopy
- double-height glazing
- porte-cochère
- steps/ramp
- major sign

Street-level identity often matters more than upper windows.

---

# BR. Signage system

Do NOT bake tenant signs directly into permanent building meshes.

Create:

```text
SignageAnchor
```

Suggested fields:

```text
id
building_id
facade
position
rotation
width_m
height_m
sign_type
text
asset
source_id
grounding
current_as_of
rights_status
visibility_priority
```

---

# BS. Sign types

Support:

```text
BUILDING_NAME
MALL_NAME
MAJOR_TENANT
STORE_FRONT
WAYFINDING
PARK_SIGN
ART_LABEL
```

---

# BT. Signage hierarchy

Render first:

1. building identity
2. mall identity
3. major anchor brand
4. visually dominant store
5. park/wayfinding signs

Do not render hundreds of tiny tenant names.

---

# BU. Trademark/logo handling

Use official logo graphics only if appropriate.

Otherwise:

- use text
- use simplified signage
- omit

Never download random logo PNGs from unknown sites.

---

# BV. Public art system

Create:

```text
ArtAnchor
```

Fields:

```text
id
title
artist
location
position
rotation
category
source
rights_status
current_status
geometry_asset
texture_asset
```

---

# BW. Current BGC art

Before final art implementation, snapshot BGC's current official Arts & Culture Directory.

Current official listings include works at locations such as:

- High Street portals
- Track 30th
- Terra 28th
- De Jesus Oval
- Mind Museum
- Rizal Drive
- 26th Street
- Gomez Circle
- Triangle Drive

Do not assume historic murals/installations are still present.

---

# BX. Sculpture

If location and shape are adequately documented:

create simplified sculptural geometry.

Maintain:

- title
- artist
- source
- location

---

# BY. Murals

Do not reproduce copyrighted mural art from research photography without reusable rights.

Instead:

- correct wall/panel location
- correct approximate size
- neutral/color-presence placeholder
- metadata

Use actual image texture only when licensing permits.

---

# BZ. Lighting families

Replace one universal pole with:

```text
LIGHT_MAIN_STREET
LIGHT_SECONDARY
LIGHT_HIGH_STREET
LIGHT_PARK_PATH
LIGHT_PLAZA
LIGHT_BOLLARD
```

Exact designs require visual matching.

---

# CA. No hundreds of dynamic lights

At daytime, street lights are geometry.

At night, prefer:

- emissive heads
- selective real lights

Do not create hundreds of shadow-casting point lights.

---

# CB. Street furniture library

Support:

```text
BENCH
PLANTER
STREETLIGHT
BOLLARD
WASTE_BIN
BIKE_RACK
BUS_SHELTER
HYDRANT
TRAFFIC_SIGNAL
STREET_SIGN
UTILITY_BOX
CCTV_POLE
TREE_GRATE
RAILING
GUARDRAIL
```

Use district-specific variants where they matter.

---

# CC. Visual clutter policy

Add enough urban clutter to feel inhabited.

Do not create noise.

Avoid:

- random cones
- excessive barriers
- dozens of unrelated advertisements
- random parked vehicles everywhere

---

# CD. Vehicles

Optional static sparse vehicles may be used for scale.

Keep:

- roads clear
- Walk routes clear
- performance controlled

Dynamic traffic is not required for M23 acceptance.

---

# CE. People

Optional.

If used:

- simple low-poly/billboard figures
- sparse distribution
- no full crowd simulation

Do not make this a blocker.

---

# CF. Detail package architecture

Do not put everything into base tile GLBs.

Maintain layers:

```text
BuildingTile
PublicRealmDetailTile
StreetscapeTile
TerrainDetailZone
LandmarkAsset
SignageLayer
ArtLayer
```

This will later make Graphics Settings straightforward.

---

# CG. Zone packages

Prefer split packages such as:

```text
/world/detail/high-street/
/world/detail/high-street-central/
/world/detail/parks/
/world/detail/one-bonifacio/
/world/detail/uptown/
/world/detail/aura/
/world/detail/mitsukoshi/
```

Do not create one giant visual-detail package.

---

# CH. Lazy loading

Detail must load only when needed.

Normal distant BGC should remain lightweight.

---

# CI. Streaming hierarchy

Conceptually:

```text
overview
→ LOD2

near zone
→ public-realm detail

closer
→ LOD1-Lite

landmark/hero range
→ LOD1
```

---

# CJ. Reference cameras

Every hero zone should have fixed QA cameras:

```text
AERIAL
STREET_FRONT
STREET_REAR
LEFT_OBLIQUE
RIGHT_OBLIQUE
```

Buildings with complex roofs should have:

```text
ROOF_OBLIQUE
```

---

# CK. Astra QA

Where Astra is available:

give Astra:

- current render
- supplied reference image(s)
- evidence notes

Ask it to return only structured discrepancies.

Suggested discrepancy schema:

```text
entity_id
camera_id
severity
category
observation
reference_evidence
recommended_change
confidence
requires_research
```

Categories:

```text
MASSING
SILHOUETTE
FACADE_RHYTHM
MATERIAL
ENTRANCE
LANDSCAPE
STREETSCAPE
TERRAIN
SIGNAGE
ART
LIGHTING
```

---

# CL. Iteration count

Use approximately:

```text
2–4 render → review → patch loops
```

per hero asset.

Stop when remaining differences are low-value or unsupported.

Do not endlessly polish.

---

# CM. Automatic candidate selection for LOD1-Lite

Do not ask the model to arbitrarily rank buildings.

Use explicit factors:

```text
visibility
named-place status
building height
pedestrian-zone proximity
architectural uniqueness
reference quality
existing search importance
```

Store factor values.

Human can review resulting candidates.

---

# CN. Height conflicts

Official architecture references can conflict with OSM/project values.

Never silently overwrite.

Store:

```text
height_claims[]
```

with:

```text
value
source
date
confidence
survey_status
```

Example:

ACPT official SOM reference says 136 m / 32 stories.

If project data differs:

mark conflict and review.

---

# CO. Performance principles

Prefer:

- instancing
- shared geometry
- shared materials
- facade kits
- geometry batching
- zone loading
- LOD

Avoid:

- one React object per tree
- one material per shop
- unique geometry for every bench
- huge textures
- permanently loaded hero zones

---

# CP. Texture policy

Prefer geometry/material changes first.

Use textures mainly for:

- important large signage
- large unique logos
- reusable pavement/roughness
- unique facade mask
- licensed art

---

# CQ. Texture resolution

Default small.

Typical guidance:

```text
small sign:
256–512

large hero sign:
512–1024

unique facade mask:
1024 only when justified
```

Avoid 4K by default.

---

# CR. Compression

If texture/GLB weight grows:

evaluate:

- KTX2/Basis
- glTF compression

Measure before adopting.

---

# CS. Performance metrics

For every zone record:

- draw calls
- triangles
- geometries
- textures
- instances
- transferred bytes
- decoded bytes where measurable

---

# CT. Walk requirements

Walk is the strongest fidelity test.

Inspect:

- curb height
- road scale
- sidewalk width
- trees
- benches
- lights
- doors/entrances
- lane width
- ramp/stair behavior
- collision
- terrain grounding
- signage scale

---

# CU. Search integration

Search focusing should prioritize:

1. base tile
2. target building
3. target terrain/public zone if necessary
4. decorative assets later

Do not block focus on a bench or shrub.

---

# CV. Tour integration

Do not automatically create a 30-stop tour.

Keep a curated set of meaningful landmarks.

---

# CW. Manual validation

User owns visual acceptance.

Codex/Astra must mark:

```text
AWAITING_USER_TEST
```

for subjective claims such as:

- looks like real BGC
- facade likeness
- streetscape likeness
- park likeness
- terrain feel
- signage correctness

---

# CX. Suggested manual validation route

Create one QA route through:

```text
Burgos Circle
→ Mind Museum
→ High Street
→ High Street Central
→ One Bonifacio
→ Track 30th
→ Terra 28th
→ SM Aura
→ Uptown
→ Mitsukoshi
```

This covers different district characters.

---

# CY. Automatic QA

Continue checking:

- zero-visible events
- repeated tile requests
- LOD gaps
- runtime errors
- Search transitions
- Tour transitions
- determinism
- provenance
- geometry validity
- object overlap
- terrain continuity
- package requests

---

# CZ. Performance benchmark

Reject invalid background-throttled runs.

Valid matched runs require identical:

- browser foreground state
- viewport
- DPR
- environment quality
- camera path
- duration
- loading state

Use multiple runs.

---

# DA. Performance guard

Investigate if detail causes more than roughly:

```text
15% median or p1 degradation
```

under matched valid conditions.

An unexplained degradation over approximately:

```text
25%
```

should block promotion.

---

# DB. Implementation milestones

Execute in this order.

## M23A — Evidence consolidation

- create reference manifest
- verify entity mapping
- record supplied source references
- flag conflicts
- identify missing critical views

No major visual generation yet.

---

## M23B — Citywide streetscape kit

Implement:

- road markings
- curbs
- drainage
- bike infrastructure
- signals
- signs
- bus stops
- utility objects
- arcades
- generic BGC lighting

---

## M23C — Landscape system

Implement:

- tree variants
- palms
- shrubs
- lawns
- groundcover
- park vegetation rules

Preserve mapped vegetation.

---

## M23D — High Street original blocks

Implement:

- paving
- landscape spine
- store fronts
- awnings
- furniture
- lights
- art anchors
- outdoor dining
- water cues

---

## M23E — High Street Central

Implement:

- terrain
- stairs
- ramps
- amphitheater
- water
- feature gardens
- GroundSampler
- Walk integration

---

## M23F — Parks

Implement distinct visual systems for:

- Track 30th
- Terra 28th
- Kasalikasan
- De Jesus Oval
- Greenway
- Burgos Circle
- JY Campos Park

---

## M23G — One Bonifacio ensemble

Implement together:

- PSE
- Suites
- Shangri-La
- One Bonifacio retail/public realm

---

## M23H — Hero landmarks

Implement/refine:

- ACPT
- Central Square
- UNIQLO
- Mind Museum
- SM Aura
- Mitsukoshi

---

## M23I — Secondary districts

Implement LOD1-Lite/public realm for:

- Uptown
- The Seasons
- High Street South
- Forbes Town
- Serendra
- Market! Market!
- Park Triangle
- University Parkway

---

## M23J — Identity layer

Implement:

- building names
- mall signs
- major tenants
- park signs
- public art anchors
- reusable licensed art
- rights-restricted placeholders

---

## M23K — Visual QA

Run:

- fixed cameras
- Astra comparison where useful
- manual Walk
- Search
- Tour
- runtime/performance tests

---

# DC. Zone acceptance

High Street PASS requires:

- green spine reads correctly
- pedestrian paving reads correctly
- low retail frontage works
- tree rhythm works
- awnings/canopies work
- public furniture feels intentional
- art anchors exist

High Street Central PASS requires:

- terrain no longer flat
- ramps/stairs visible
- amphitheater recognizable
- water/plaza recognizable
- Walk follows ground

Park PASS requires:

- Track 30th looks unlike Terra 28th
- Terra 28th looks unlike Kasalikasan
- Greenway looks like a linear green corridor
- Burgos Circle reads as a circular cafe/residential district

Landmark PASS requires:

- recognizable massing
- recognizable facade rhythm
- recognizable base
- recognizable crown/roof
- credible material family
- major signage where appropriate

---

# DD. M23 completion target

M23 is complete when the model is recognizably BGC at both:

```text
aerial scale
```

and:

```text
pedestrian Walk scale
```

without needing photorealistic models.

The user should be able to recognize major places such as:

- High Street
- High Street Central
- Track 30th
- Terra 28th
- Kasalikasan
- Mind Museum
- One Bonifacio/PSE/Shangri-La
- SM Aura
- Uptown
- Mitsukoshi
- Burgos Circle

primarily from their modeled visual identity.

---

# DE. Reports

Create/update:

```text
docs/visual/M23_BGC_CITYWIDE.md
docs/visual/M23_HIGH_STREET.md
docs/visual/M23_HIGH_STREET_CENTRAL.md
docs/visual/M23_PARKS.md
docs/visual/M23_ONE_BONIFACIO.md
docs/visual/M23_HERO_LANDMARKS.md
docs/visual/M23_SECONDARY_DISTRICTS.md
docs/visual/M23_VISUAL_ACCEPTANCE.md
```

Avoid unnecessary report fragmentation.

Machine reports:

```text
data/reports/m23-zone-status.json
data/reports/m23-landmark-status.json
data/reports/m23-reference-coverage.json
data/reports/m23-performance.json
data/reports/m23-visual-acceptance.json
```

---

# DF. Zone lifecycle

Each zone:

```text
UNRESEARCHED
RESEARCHED
READY_WITH_GAPS
IMPLEMENTING
READY_FOR_VISUAL_QA
APPROVED
DEFERRED
```

---

# DG. Reference coverage

Track:

```text
massing
facade_north
facade_east
facade_south
facade_west
roof
ground_floor
public_realm
landscape
terrain
signage
art
night
```

with:

```text
GOOD
PARTIAL
WEAK
NONE
```

Codex may research only a critical `NONE`.

---

# DH. Final rule

Build BGC by **identity**, not by object density.

Priority:

```text
correct place
↓
correct massing
↓
correct terrain
↓
correct public realm
↓
correct ground-floor interface
↓
correct facade rhythm
↓
correct landscape
↓
correct signage/art
↓
minor detail
```

A small number of correct cues is more valuable than thousands of generic objects.

Do not begin Graphics Settings yet.

After M23 user acceptance, the next milestone is:

```text
M24 — Graphics Settings
```

with eventual presets such as:

```text
Performance
Balanced
Quality
```

mapped onto the new detail layers.

Stop after M23 and request user visual validation.