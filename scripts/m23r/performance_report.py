"""Seal final runtime/assets, then validate the 3 x 5 foreground benchmark set."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PROFILES=['performance','balanced','quality']
ROUTES=['explore-high-street','explore-uptown','walk-high-street','walk-central','tour']
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,d):(ROOT/p).write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def fingerprint():
 paths=[]
 for folder in ['web/components','web/app','web/public/models','web/public/world','web/public/signage']:
  paths.extend(p for p in (ROOT/folder).rglob('*') if p.is_file())
 files={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
 return dict(sha256=hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest(),files=files,production_build_id=(ROOT/'web/.next/BUILD_ID').read_text().strip())
def main():
 if '--seal' in sys.argv:
  write('data/reports/m23r-final-fingerprint.json',fingerprint());print('Final runtime and asset fingerprint sealed');return
 seal=read('data/reports/m23r-final-fingerprint.json');current=fingerprint();runs=[];missing=[];invalid=[]
 for profile in PROFILES:
  for route in ROUTES:
   path=f'data/reports/m23r-browser/{profile}-{route}.json'
   if not (ROOT/path).exists():missing.append(path);continue
   run=read(path);runs.append(dict(profile=profile,route=route,report=run))
   if run['status']!='PASS' or run['graphics']['preset']!=profile or run['environment']['viewport']!='1000x760':invalid.append(path)
 unchanged=seal['sha256']==current['sha256'] and seal['production_build_id']==current['production_build_id']
 summary={profile:dict(runs=sum(r['profile']==profile for r in runs),mean_fps_range=[min([r['report']['mean_fps'] for r in runs if r['profile']==profile],default=0),max([r['report']['mean_fps'] for r in runs if r['profile']==profile],default=0)],p1_low_fps_range=[min([r['report']['p1_low_fps'] for r in runs if r['profile']==profile],default=0),max([r['report']['p1_low_fps'] for r in runs if r['profile']==profile],default=0)]) for profile in PROFILES}
 result=dict(status='PASS' if len(runs)==15 and not missing and not invalid and unchanged else 'PARTIAL',required_runs=15,completed_runs=len(runs),missing=missing,invalid=invalid,final_fingerprint_unchanged=unchanged,final_fingerprint=seal['sha256'],production_build_id=seal['production_build_id'],protocol='Production build, visible foreground browser, fixed 1000x760 CSS viewport, profile DPR recorded, 5s warmup + 15s sample, deterministic finite motion, camera path fixed per route across profiles.',profiles=summary,runs=runs,limitations=['Renderer counts are measured at the final sample, not peak allocation.','Results describe this machine and viewport, not a device-wide performance guarantee.','The earlier walk-route smoke test is excluded because generation/render work was still running.'])
 write('data/reports/m23r-performance.json',result);print(result['status'],len(runs),'runs; unchanged:',unchanged)
if __name__=='__main__':main()
