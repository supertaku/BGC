"""Regenerate the complete web pipeline twice and compare byte hashes."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
COMMANDS=['scripts/m23/build.py','scripts/m23r/building_facades.py','scripts/m23r/identity.py','scripts/m23r/benchmark_routes.py']
def snapshot():
 paths=[]
 for folder in ['web/public/world/detail/m23','web/public/world/detail/m23r','web/public/models/m23r','data/visual_reference/features']:
  paths.extend(p for p in (ROOT/folder).rglob('*') if p.is_file())
 return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
def main():
 commands=[[script] for script in COMMANDS]
 incremental='--landmark' in sys.argv
 if incremental:
  key=sys.argv[sys.argv.index('--landmark')+1]
  commands=[['scripts/m23r/rebuild_landmark.py',key],['scripts/m23r/identity.py']]
 if '--streets' in sys.argv:
  incremental=True
  commands=[['scripts/m23r/rebuild_streets.py'],['scripts/m23r/identity.py']]
 runs=[]
 for iteration in range(2):
  for command in commands:subprocess.run([sys.executable,*command],cwd=ROOT,check=True)
  runs.append(snapshot());print('Completed regeneration',iteration+1,flush=True)
 differences=[p for p in sorted(set(runs[0])|set(runs[1])) if runs[0].get(p)!=runs[1].get(p)]
 report={'status':'FAIL' if differences else 'PASS','runs':2,'compared_files':len(runs[1]),'differences':differences,'hashes':runs[1],'scope':'Web JSON packages, feature provenance, procedural facade GLBs and benchmark routes. Offline Blender preview binaries are excluded.'}
 report['generation_commands']=commands
 if incremental:report['retained_full_pipeline_report']='data/reports/m23r-determinism-full.json'
 (ROOT/'data/reports/m23r-determinism.json').write_text(json.dumps(report,indent=2)+'\n')
 print(report['status'],report['compared_files'],'files',flush=True)
 if differences:raise SystemExit(1)
if __name__=='__main__':main()
