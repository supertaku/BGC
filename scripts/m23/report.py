"""Derive the M23 handoff ledger without granting subjective approval."""
import hashlib,json,statistics
from pathlib import Path
from prepare import ROOT,read,write

def main():
 cat=read('web/public/world/detail/m23/catalog.json');targets=read('data/visual_reference/targets.json')['targets'];sources=read('data/visual_reference/manifest.json')['sources']
 validation=read('data/reports/m23-validation.json');perf=read('data/reports/m23-performance.json')
 runs_path=ROOT/'data/reports/m23/browser-benchmarks.json'
 runs=json.loads(runs_path.read_text()) if runs_path.exists() else []
 perf['browser_runs']=runs;perf['valid_runs']=sum(r.get('status')=='PASS' for r in runs)
 comparisons=[]
 for mode in ['INSPECT','WALK']:
  selected={key:[r for r in runs if r.get('status')=='PASS' and r.get('navigation')==mode and r.get('preview_mode')==key] for key in ['baseline','m23']}
  off,on=selected['baseline'],selected['m23']
  if not off or not on:continue
  med=lambda rs,k:statistics.median(r[k] for r in rs)
  change={k:round(100*(med(off,k)-med(on,k))/med(off,k),2) for k in ['median_fps','p1_low_fps']}
  matched=len({(r['environment']['viewport'],r['environment']['device_pixel_ratio'],r['environment']['gpu'],r['scene'],r['quality'],r['mode']) for r in off+on})==1
  enough=len(off)>=3 and len(on)>=3 and matched
  comparisons.append(dict(navigation=mode,baseline_runs=len(off),m23_runs=len(on),matched_environment=matched,baseline_median_fps=med(off,'median_fps'),m23_median_fps=med(on,'median_fps'),baseline_p1=med(off,'p1_low_fps'),m23_p1=med(on,'p1_low_fps'),degradation_percent=change,status='BLOCK' if max(change.values())>25 else 'INVESTIGATE' if max(change.values())>15 else 'PASS' if enough else 'MORE_MATCHED_RUNS_REQUIRED'))
 perf['comparisons']=comparisons
 perf['walk_route']='Existing deterministic benchmark_walk route: default Walk spawn near [-90, 1.7, 170], 7 m/s for 20 s; require >=100 m displacement. It is a repeatable streaming sample, not the complete ten-stop visual route.'
 perf['inspect_revision_note']='Three initial matched Inspect pairs preceded the final mapped-tree crown and local terrain repairs. Final moving Walk runs include those runtime changes; Inspect observations are retained with this limitation.'
 complete=len(comparisons)==2 and all(c['status']=='PASS' for c in comparisons)
 perf['status']='MATCHED_FOREGROUND_PASS' if complete else 'VALID_INSPECT_SAMPLES_WALK_COMPARISON_PENDING' if perf['valid_runs'] else 'MATCHED_FOREGROUND_RUNS_REQUIRED'
 perf['promotion']='AWAITING_USER_TEST' if complete else 'BLOCKED_PENDING_PERFORMANCE_AND_USER_ACCEPTANCE'
 perf['notes']+=' Browser detail field belongs to the legacy detail=1 manager; use URL/run labels and renderer metrics for M23. Chrome background samples with THROTTLED_FRAME were rejected.'
 write('data/reports/m23-performance.json',perf)
 fields=['massing','facade_north','facade_east','facade_south','facade_west','roof','ground_floor','public_realm','landscape','terrain','signage','art','night']
 coverage=[];landmarks=[];zones=[]
 for e in cat['packages']:
  fs=read(f'data/visual_reference/features/{e["id"]}.json');source_ids=sorted({s for f in fs for s in f['source_ids']});known=[s for s in sources if s['source_id'] in source_ids]
  photos=any(s['source_id'].startswith('user_photo') for s in known)
  levels={k:'NONE' for k in fields};levels.update(massing='GOOD' if e['kind']=='landmark' else 'PARTIAL',public_realm='PARTIAL',landscape='PARTIAL')
  if e['kind']=='landmark':levels.update(roof='PARTIAL',ground_floor='PARTIAL',signage='PARTIAL')
  if photos:levels.update(ground_floor='PARTIAL',roof='PARTIAL')
  # Cardinal orientation is not established by supplied oblique photos.
  for k in fields:
   if k.startswith('facade_'):levels[k]='WEAK' if photos else 'NONE'
  if e['id']=='high_street_central':levels['terrain']='PARTIAL'
  coverage.append(dict(zone_id=e['id'],coverage=levels,source_ids=source_ids,unverified='Unseen facades, exact dimensions, tenant inventory, current artwork placement and night lighting.'))
  zone=dict(zone_id=e['id'],state='READY_FOR_VISUAL_QA',acceptance='AWAITING_USER_TEST',source_ids=source_ids,feature_count=len(fs),package_url=e['url'])
  zones.append(zone)
  if e['kind']=='landmark':landmarks.append({**zone,'entity_id':e.get('entity_id'),'name':e.get('name'),'replaced_canonical_ids':e.get('replaces',[]),'height_m':e.get('height_m'),'fidelity':'LOD1_LITE' if e['id'].startswith('lite_') else 'M23_LANDMARK_PREVIEW','approved_registry':False})
 write('data/reports/m23-zone-status.json',dict(status='AWAITING_USER_TEST',zones=zones))
 write('data/reports/m23-landmark-status.json',dict(status='AWAITING_USER_TEST',landmarks=landmarks))
 write('data/reports/m23-reference-coverage.json',dict(status='EVIDENCE_WITH_EXPLICIT_GAPS',sources=len(sources),zones=coverage))
 cameras=[read(str(p.relative_to(ROOT))) for p in sorted((ROOT/'data/reports/m23/cameras').glob('*.json'))]
 gaps=['Precise High Street Central elevations are estimated, not surveyed.', 'Artwork anchors are recorded; protected murals/sculptures are not reproduced and uncertain positions remain unset.', 'Unseen landmark elevations and exact tenant/brand graphics remain inferred.', 'Shangri-La bridges and elevated arrival arrangement need stronger placement evidence; current shared court/terrace is an approximation.', 'User appearance acceptance remains a promotion gate.' if complete else 'Valid matched moving Walk benchmarks and user appearance acceptance remain promotion gates.']
 acceptance=dict(status='AWAITING_USER_TEST',engineering_validation=validation['status'],approved_assets_preserved=7,default_enabled=False,m24_started=False,cameras=cameras,known_gaps=gaps,route=['High Street','High Street Central','Track 30th','Terra 28th','Kasalikasan','One Bonifacio ensemble','Mind Museum','SM Aura','Mitsukoshi / Seasons','Uptown / Burgos Circle'])
 write('data/reports/m23-visual-acceptance.json',acceptance)
 hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'scripts/m23').glob('*.py'))}
 write('data/reports/m23/source-hashes.json',dict(scripts=hashes,inputs={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'data/visual_reference/targets.json',ROOT/'data/visual_reference/manifest.json',ROOT/'data/assets/buildings.json']}))
 docs={
 'BGC_CITYWIDE':('Citywide implementation',f'{len(cat["packages"])} spatial packages supply mapped building massing, façade families, street markings, safe edge furniture, seven tree archetypes and landscape detail. Geometry is merged by material and primitives are instanced across active packages. Runtime source records are stored separately under data/visual_reference/features. The kit gallery is a reusable source library and is not loaded into the city.','Road markings use mapped lane/cycleway/crossing tags. Intersection signal positions are inferred from mapped nodes and relocated to clear road edges. Unmapped bike lanes and traffic arrangements are not fabricated.'),
 'HIGH_STREET':('High Street','Mapped pedestrian polygons drive paving fields, border bands and joints. Low retail façades, glazing, canopies, tree rhythm, planting and mapped outdoor seating support the pedestrian corridor. Art anchors retain directory attribution.','Photo 1 supports the broad tree canopy, layered planting, dark planters and low retail interface. Individual storefronts and furniture dimensions remain inferred.'),
 'HIGH_STREET_CENTRAL':('High Street Central','A local terraced amphitheater, water center, radial paving, stairs and outer grade apron replace the flat preview. The shared GroundSampler registers triangulated height surfaces while the package is active, and Walk samples these surfaces every frame. Local terrain falls back to the existing city ground when unloaded. Mapped low-detail props intersecting raised terrain are temporarily suppressed; canonical mapped records are retained.','The Crearis reference establishes amphitheater, water, plaza and garden identity. All elevations and detailed arrangement are estimated, including the apron gradient; no accessible-gradient certification is claimed. Constrained triangulation and a boundary tolerance repair the gaps seen in earlier fixed-camera iterations. The intrusive inner ramp wedge was removed.'),
 'PARKS':('Distinct park families','Track 30th uses exercise/loop cues and its yellow identity sign; Terra 28th uses play pads and open lawn; Kasalikasan uses concentric planted terraces and a raised circular stage. De Jesus Oval, Greenway, Burgos Circle and the museum park have separate packages tied to mapped boundaries.','Park identities and broad features have official references. Exact apparatus, tree positions, stage heights and play-pad layouts are inferred. Directory art entries are location metadata, not exact sculpture replicas.'),
 'ONE_BONIFACIO':('One Bonifacio ensemble','PSE, The Suites, Shangri-La and the retail podium retain their mapped canonical volumes with separate material rhythms, bases and crowns. A shared public-realm package supplies courts and an estimated raised terrace. An ensemble render checks their combined silhouette.','PSE identity bands/ribs, Suites balcony rhythm and Shangri-La stone podium use the reference cues. Three glass bridges and the precise arrival sequence require stronger spatial evidence and remain a documented gap.'),
 'HERO_LANDMARKS':('Hero landmarks','PSE ribs and identity band; Suites balcony layers; Shangri-La stepped volumes and stone base; ACPT overlapping glass/crown planting; Museum curved roof and slanted supports; Aura roof ribbons, garden, egg hall and arched chapel; Mitsukoshi lattice podium and Seasons towers are authored as distinct packages. Uniqlo retains its low retail identity.','The ACPT 114.7 m outline conflicts with its 136 m mapped part/official source; the conflict is retained and the taller part is used. All unseen elevations, fixture spacing and secondary roof details are inferred. No new package is inserted into the approved LOD1 registry.'),
 'SECONDARY_DISTRICTS':('Secondary districts','Uptown Mall, One Uptown Residence, Parksuites, Market! Market! and three Serendra blocks have dedicated packages. Forbes Town, University Parkway and McKinley Parkway use named mapped corridors. Fourteen scored LOD1-Lite candidates receive type-based façade treatment with provenance and no invented architectural verification.','Unavailable official pages remain marked as such in the manifest. Candidate uniqueness is not claimed. The existing seven approved LOD1 assets retain their original loading and Tour behavior.'),
 'VISUAL_ACCEPTANCE':('Visual acceptance',f'Status: AWAITING_USER_TEST. Static content validation: {validation["status"]}. Open /?detail=m23&debug=1 for the opt-in preview. Normal LOW remains the baseline; detail=1 remains the earlier preview. The eight reports and machine ledgers are regenerated by scripts/m23/report.py.','Use the route below to review identity, ground continuity, entrances, planting and façade rhythm. User appearance approval is separate from engineering checks. M24 has not started.')}
 for key,(title,body,limits) in docs.items():
  text=f'# M23 — {title}\n\n{body}\n\n## Evidence and limits\n\n{limits}\n\n## Reproduce\n\nRun `scripts/m23/run.ps1 -Render` from the repository. Source geometry is in `scripts/m23/build.py`; runtime packages are in `web/public/world/detail/m23`; fixed cameras and hashes are in `data/reports/m23`. Generated Blender and GLB outputs can be recreated.\n\n## Validation\n\nSee `data/reports/m23-validation.json`, `m23-performance.json`, `m23-reference-coverage.json` and `m23-visual-acceptance.json`. Static PASS does not grant appearance approval.\n'
  if key=='VISUAL_ACCEPTANCE':text+='\n## Review route\n\n'+'\n'.join(f'{i+1}. {x}' for i,x in enumerate(acceptance['route']))+'\n\n## Known gaps\n\n'+'\n'.join('- '+x for x in gaps)+'\n'
  (ROOT/f'docs/visual/M23_{key}.md').write_text(text,encoding='utf-8')
 print(f'M23 reports: {len(zones)} zones, {len(landmarks)} landmarks, {len(cameras)} camera sets; AWAITING_USER_TEST')

if __name__=='__main__':main()
