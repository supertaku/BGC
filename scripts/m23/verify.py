"""Validate finite geometry, provenance, replacement coverage, budgets and hashes."""
import gzip,hashlib,json,math
from collections import Counter
from prepare import ROOT,read,write

def main():
 cat=read('web/public/world/detail/m23/catalog.json');sources={s['source_id'] for s in read('data/visual_reference/manifest.json')['sources']};failures=[];metrics=[];claimed=set()
 for e in cat['packages']:
  path=ROOT/'web/public'/e['url'].lstrip('/');d=json.loads(path.read_text(encoding='utf-8'));features=read(f'data/visual_reference/features/{e["id"]}.json');ids={f['feature_id'] for f in features}
  for f in features:
   if not f['source_ids'] or any(s not in sources and not s.startswith('osm:') for s in f['source_ids']):failures.append(f"{e['id']}: unresolved sources {f['source_ids']}")
   if f['grounding'] not in ['INFERRED','ESTIMATED','VERIFIED_GEOGRAPHIC','VERIFIED_VISUAL','PROCEDURAL','UNKNOWN','CONFLICTED']:failures.append(f"{e['id']}: grounding")
  triangles=0
  for mat,m in d['meshes'].items():
   v=m['vertices'];ind=m['indices'];triangles+=len(ind)//3
   if mat not in d['materials'] or len(v)%3 or len(ind)%3 or not all(math.isfinite(n) for n in v) or any(i<0 or i>=len(v)//3 for i in ind):failures.append(f"{e['id']}: invalid mesh {mat}")
  for i in d['instances']:
   if i['feature_id'] not in ids or min(i['scale'])<=0 or not all(math.isfinite(v) for v in i['position']+i['scale']+[i['yaw']]):failures.append(f"{e['id']}: invalid instance {i['feature_id']}")
   triangles+=dict(box=12,sphere=64,cylinder=40,cone=20)[i['kind']]
  for sid in e.get('replaces',[]):
   if sid in claimed:failures.append(f'Duplicate replacement: {sid}')
   claimed.add(sid)
  groups={(i['kind'],i['material']) for i in d['instances']};textures=min(3,len(d['signs']))
  metrics.append(dict(zone_id=e['id'],draw_calls=len(d['meshes'])+len(groups)+textures,triangles=triangles,geometries=len(d['meshes'])+len(groups)+textures,textures=textures,texture_memory_bytes=textures*512*128*4*4//3,instances=len(d['instances']),raw_bytes=path.stat().st_size,gzip_bytes=len(gzip.compress(path.read_bytes(),mtime=0)),decoded_geometry_bytes=sum(len(m['vertices'])*8+len(m['indices'])*4 for m in d['meshes'].values())+len(d['instances'])*64,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
 for p in (ROOT/'data/assets/manifests').glob('*lod1.json'):
  if not p.exists():failures.append('Missing approved asset')
 registry=read('data/assets/buildings.json');approved=[k for k,v in registry['buildings'].items() if v['available_lods'].get('1',{}).get('status')=='APPROVED']
 if len(approved)!=7:failures.append('Approved registry no longer contains seven assets')
 ground=read('web/public/world/detail/m23/high_street_central.json')['terrain']
 if not ground or max(p[1] for t in ground for p in t['points'])<1:failures.append('Terrain remains flat')
 report=dict(status='PASS' if not failures else 'FAIL',failures=failures,packages=len(cat['packages']),preserved_approved_assets=approved,ground_triangles=len(ground),scope='Static content and contract checks, not subjective acceptance or foreground FPS')
 write('data/reports/m23-validation.json',report)
 write('data/reports/m23-performance.json',dict(status='MATCHED_FOREGROUND_RUNS_REQUIRED',promotion='BLOCKED_PENDING_PERFORMANCE_AND_USER_ACCEPTANCE',zones=metrics,totals={k:sum(m[k] for m in metrics) for k in ['triangles','instances','raw_bytes','gzip_bytes','texture_memory_bytes']},budget_policy='Investigate >15% matched median/p1 degradation; unexplained >25% blocks promotion. Per-zone metrics are estimates; renderer metrics come from browser.',notes='Only nearby packages allocate geometry. GPU instance buffers are counted; JS object overhead is not measured. Text signs use 512x128 canvas textures.'))
 print(json.dumps(report,indent=2));
 if failures:raise SystemExit(1)
if __name__=='__main__':main()
