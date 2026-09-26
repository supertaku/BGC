"""Summarize evidence without converting unverified visual claims into passes."""
import json,hashlib
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,d):
 path=ROOT/p;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def doc(name,text):(ROOT/'docs'/name).write_text(text.strip()+'\n',encoding='utf-8')
def main():
 cat=read('web/public/world/detail/m23/catalog.json');features=[]
 for p in (ROOT/'data/visual_reference/features').glob('*.json'):
  if p.stem!='city_kit':features.extend(read(p.relative_to(ROOT)))
 kinds=Counter(f['feature_id'].split(':')[-2] for f in features)
 roadkeys=['LANE_DIVIDER','TURN_ARROW','ROAD_EDGE_LINE','ZEBRA_CROSSING','CROSSING_STOP_BAR','BIKE_SYMBOL','BIKE_BOLLARD','GUTTER','STORM_INLET','CURB_STANDARD','TRAFFIC_SIGNAL','LIGHT_HIGH_STREET']
 roads=read('data/processed/bgc-roads.geojson')['features']
 write('data/reports/m23r-road-detail.json',dict(status='READY_FOR_USER_VALIDATION',feature_counts={k:kinds[k] for k in roadkeys},all_feature_counts=dict(sorted(kinds.items())),mapped_roads=len(roads),roads_with_lane_count=sum(str(f['properties'].get('tags',{}).get('lanes','')).isdigit() for f in roads),grounding='Mapped alignments and explicit lane/cycleway tags; furniture intervals, dimensions and exact placement inferred.',limitations=['Stop-bar locations are inferred on mapped crossing approaches with explicit lane counts.','Crossings are oriented to mapped polygons; missing lane counts are not invented.'],fixture_gallery_excluded=True))
 coverage=read('data/reports/m23r-building-coverage.json');facade=read('data/reports/m23r-facade-stability.json');realm=read('data/reports/m23r-public-realm.json');signs=read('data/reports/m23r-signage.json');art=read('data/reports/m23r-art.json')
 cameras=[]
 for entry in cat['packages']:
  if entry['kind']!='landmark':continue
  folder=ROOT/'blender/renders/m23/m23r'/entry['id'];views=sorted(p.stem for p in folder.glob('*.png'))
  cameras.append(dict(id=entry['id'],views=views,static_geometry_review='REVIEWED' if len(views)==6 else 'MISSING',live_flicker='AWAITING_USER_TEST'))
 write('data/reports/m23r-visual-review.json',dict(status='AWAITING_USER_TEST',landmarks=cameras,review_sheets='data/reports/m23r-review',limitations=['Contact sheets verify massing coverage and obvious gaps, not animated flicker or photographic equivalence.','Mitsukoshi and The Seasons are separate packages and must be evaluated together in the city.','Smaller LOD1-Lite buildings intentionally retain simplified inferred detail.']))
 nav=dict(status='PARTIAL',implemented=['fixed-position right-drag look','right-held WASD horizontal flight','left-drag pan','view-direction wheel zoom','pitch +/-85 degrees','maximum altitude 2800m','GroundSampler clearance','pointer capture/cancel/blur cleanup','Search transition interruption','three radio graphics presets','localStorage bgc.graphics.v1; URL override','no Canvas remount','exact Explore instructions in public Help'],automated_tests='web/scripts/verify-m24.mjs and verify-street-controls.mjs PASS',browser_verified=['Graphics dialog keyboard selection updates URL','Quality switch preserves camera position','Escape closes Graphics','Help displays all four exact Explore instructions'],manual_remaining=['Right-button held flight and camera feel','Full Search interruption interaction sequence','Profile visual difference at representative locations'])
 write('data/reports/m24-navigation-graphics.json',nav)
 doc('visual/M23R_RENDER_STABILITY.md',f'''# M23R render stability

The landmark shell compiler unions duplicate fronts, clips competing coplanar surfaces, removes identical internal joints, and keeps opaque materials FrontSide. It does not rely on global polygon offset. Structural glazing has physical separation from the mass.

Current audit: **{facade['status']}**, tolerance 0.02m. Counts: `{json.dumps(facade['counts'])}`. Scope includes vertical triangles, box faces and landmark sign planes. Opposing construction joins are retained as intentional overlays. Ground and roof overlap are outside this vertical-facade audit.

Explore uses near 0.4m / far 8000m, Walk near 0.08m; reversed depth is requested and the actual GPU support is captured with each benchmark. Unsupported GPUs retain Three.js's normal depth path.

All 31 landmarks have six fixed camera renders. The eight contact sheets in `data/reports/m23r-review` were inspected. Live near/far flicker remains **AWAITING_USER_TEST**.
''')
 doc('visual/M23R_BUILDING_FIDELITY.md',f'''# M23R building fidelity

{coverage['covered_buildings']:,} / {coverage['canonical_buildings']:,} canonical building records receive a stable seeded facade family across {coverage['tiles']} tiles. There are {len(coverage['families'])} facade families. One exact coincident source relation shares the geometric facade of its matching relation; see the coverage report. Source types remain UNKNOWN where unsupported; their generated appearance is procedural filler.

The shader adds glazing rhythm, solid bands, fins, balcony cues, parking screens, ground-floor treatment and roof edges without geometric windows. Original footprint geometry and metadata remain intact. Approved seven assets and all 31 M23 landmarks retain their model identity while the owning tile is visible. Near furniture density and range vary independently.

M23 replacements are cached per package, kept mounted after loading, and only hide fallback geometry after React commits a ready replacement. The original approved landmark manager also follows owner-tile visibility. Request failures retain fallback geometry.

Generated outputs: `web/public/models/m23r/tiles`; manifest: `web/public/world/detail/m23r/tile-variants.json`; provenance and families: `data/reports/m23r-building-coverage.json`. Designs marked inferred/procedural are not photographic reconstructions.
''')
 doc('visual/M23R_HIGH_STREET_COMPLETION.md',f'''# M23R High Street completion

The explicit hero envelope follows mapped High Street pedestrian polygons buffered 18m and clipped to the authored area. It is an estimated working boundary, not a surveyed property boundary.

Non-building area: {realm['area_m2']:,.2f} m². Classified coverage: {min(100,realm['covered_percent']):.2f}%. Unknown: {realm['unknown_percent']:.2f}%. Holes above 4m²: {len(realm['holes_over_4m2'])}. Classification overlaps: {realm['overlap_percent']:.2f}%. Connecting paving added: {realm['added_connecting_paving_m2']:,.2f} m².

The exact polygon partition is retained in `data/visual_reference/m23r-high-street-surfaces.geojson`. Elevated grass, flat stair treads and sloping apron are classified from the rendered triangle projections. This coverage calculation does not by itself prove that every rendered ground layer is free of overlap.

Terrace grass, handrails, benches, bins, lights, planters and palms supplement the existing landscaping and GroundSampler terrain. Furniture pocket placement is inferred with building, road and through-route clearance. The four supplied photographs are hashed under `data/visual_reference/m23r/references`.

Shangri-La now includes three vertically stacked glazed bridges, arrival paving/fountain and an estimated ramped passage. The bridge count and arrangement are supported by Handel's photographs; dimensions and placement are estimated. Manual terrain and visual acceptance: AWAITING_USER_TEST.
''')
 doc('visual/M23R_ROAD_ENVIRONMENT.md',f'''# M23R roads and environment

Lane divisions and arrows are generated only where retained source lane/turn tags support them. Crosswalk stripes align with the mapped crossing polygon. Cycleway symbols and protected-lane bollards depend on explicit cycleway tags. Gutters and drainage fixtures use inferred spacing along mapped major roads.

Feature inventory: `data/reports/m23r-road-detail.json` excludes the unplaced fixture gallery. Stop bars use mapped crossing approaches with explicit lane counts; their setback is inferred. Existing curb openings remain cut around mapped pedestrian routes. No claim of surveyed road markings is made.
''')
 doc('visual/M23R_SIGNAGE_ART.md',f'''# M23R signage and art

Official BGC directory snapshot: {signs['directory_counts']}. HTML pages and hashes are retained under `data/visual_reference/m23r/directory`. Directory entries alone are not evidence of an exterior sign.

There are {signs['anchors']} sign anchors, {signs['official_logos']} authentic official logo assets and {signs['verified_visible']} photograph-backed visible brand anchors. Other existing building/park names retain explicit unverified-placement metadata. Sign texture requests and text textures are cached; the old three-sign cap is removed. Identity signs persist; minor signs are range-limited by graphics preset.

Mitsukoshi uses the official brand mark region, omitting an unrelated Tokyo store descriptor. UNIQLO's official photograph supports a temporary lawn installation, not a storefront facade or a claim that it still exists today. Its continued presence is explicitly unverified.

All {art['directory_entries']} current directory artworks are accounted for with neutral nearby-location markers. Exact positions are estimated from published locations; artwork imagery is not reproduced. Source links, rights status, artist information when available, and placement uncertainty accompany each record.

Sign accuracy and current physical presence remain AWAITING_USER_TEST. Source verification is intentionally PARTIAL rather than asserting that estimated placements are verified.
''')
 doc('M24_GRAPHICS_NAVIGATION.md', '''# M24 graphics and navigation

Explore Help exposes exactly: Left drag — Pan; Right drag — Look around; Hold Right Mouse + WASD — Fly; Scroll — Zoom.

Right drag changes yaw/pitch at a fixed camera position, clamps pitch to ±85 degrees and removes roll. WASD moves horizontally only while the right pointer is held, normalizes diagonals, and uses delta time and altitude-based speed. Left drag pans on a horizontal plane; zoom follows the viewing direction. World bounds, terrain clearance and a 2800m ceiling constrain translation. Pointer capture, cancel, lost capture, window blur and UI focus release active controls. Tour mounts no Explore/Walk input controller; Walk retains PointerLock and GroundSampler.

Performance, Balanced (Recommended), and Quality change DPR, shadows, fine-detail range/density, vegetation density, art range and water roughness. Identity geometry, major signs and terrain remain enabled for every preset. Presets are validated from `?graphics=` first, then `bgc.graphics.v1` localStorage, then Balanced. The radio dialog supports keyboard navigation, Escape, focus trapping and focus restoration. Changing settings does not remount Canvas or reset navigation, camera or Search.

The pure logic and configuration tests pass. Browser testing confirms keyboard profile selection, URL update, camera preservation, Escape and exact Help text. Full held-right-button feel and profile visual acceptance remain AWAITING_USER_TEST.

Benchmark routes are debug-only, derived from mapped/constructed walking surfaces, use one shared 20-second clock (5-second warmup + 15-second sample), and stop at its end. Walk reports cumulative travelled distance rather than straight-line displacement. Background, throttled, changed-viewport/DPR, runtime-error and incomplete-walk runs are invalid.
''')
 doc('visual/M23R_VISUAL_ACCEPTANCE.md', '''# M23R–M24 acceptance

Automated implementation remains PARTIAL until every required final performance route is resolved. The building coverage and vertical facade stability gates pass. Static six-camera geometry review covers all 31 landmarks; it does not replace manual visual acceptance.

Review evidence: `data/reports/m23r-visual-review.json`, `m23r-facade-stability.json`, `m23r-building-coverage.json`, `m23r-public-realm.json`, `m23r-road-detail.json`, `m23r-signage.json`, `m23r-art.json`, `m24-navigation-graphics.json` and the final `m23r-performance.json`.

Manual gates all remain AWAITING_USER_TEST: facade flicker; distance fidelity; generic building improvement; High Street environment; road realism; logo/sign accuracy; Explore camera feel; graphics visual difference.

No subsequent milestone has been started.
''')
 final_path=ROOT/'data/reports/m23r-performance.json'
 if final_path.exists() and read(final_path.relative_to(ROOT))['status']=='PASS':
  nav['status']='READY_FOR_USER_VALIDATION'
  nav['browser_verified'] += ['Left pan and view-direction wheel zoom', 'Search focus interrupted by canvas pan: one cancellation, no restart', 'Graphics focus trap and restoration', 'Full seven-stop Tour: seven transitions complete, no visibility gaps or repeated requests']
  nav['manual_remaining']=['Right-button held flight and camera feel','Profile visual difference at representative locations']
  write('data/reports/m24-navigation-graphics.json',nav)
  path=ROOT/'docs/visual/M23R_VISUAL_ACCEPTANCE.md'
  path.write_text(path.read_text().replace('Automated implementation remains PARTIAL until every required final performance route is resolved.', 'Final performance verification PASS: all 15 production runs are valid and the sealed runtime/assets fingerprint is unchanged. Automated engineering gates pass; exhaustive live distance-range screenshots and held-right-button interaction remain unverified.'),encoding='utf-8')
  path=ROOT/'docs/M24_GRAPHICS_NAVIGATION.md'
  path.write_text(path.read_text().replace('Escape and exact Help text.', 'Escape, focus trapping/restoration, exact Help text, left pan, view-direction zoom and Search interruption without restart. The full seven-stop Tour completed without visibility gaps or repeated requests.'),encoding='utf-8')
 print('Completion reports written with explicit verification limits')
if __name__=='__main__':main()
