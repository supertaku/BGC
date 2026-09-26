"""Record the repository baseline and validate facade depth competition."""
import hashlib,json,math,subprocess,sys
from pathlib import Path
from collections import defaultdict,Counter
import numpy as np
from shapely.geometry import Polygon
from shapely.strtree import STRtree
ROOT=Path(__file__).resolve().parents[2]
def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def write(path,value):
 p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def command(*args):return subprocess.check_output(args,cwd=ROOT,text=True).strip()

def faces(package):
 for sign in package.get('signs',[]):
  x,y,z=sign['position'];w=sign.get('physical_width_m',sign['width_m']);h=sign.get('physical_height_m',sign['height_m']);angle=sign['rotation'][1];c,s=math.cos(angle),math.sin(angle)
  points=np.array([[x+u*w*c,y+v*h,z-u*w*s] for u,v in [(-.5,-.5),(.5,-.5),(.5,.5),(-.5,.5)]])
  yield 'SIGN',f'sign:{sign["id"]}',points,False
 for mat,mesh in package['meshes'].items():
  v=np.array(mesh['vertices']).reshape(-1,3)
  for n in range(0,len(mesh['indices']),3):yield mat,f'mesh:{mat}:{n//3}',v[mesh['indices'][n:n+3]],False
 for number,i in enumerate(package['instances']):
  if i['kind']!='box':continue
  x,y,z=i['position'];sx,sy,sz=i['scale'];a=i['yaw'];c,s=math.cos(a),math.sin(a)
  v=np.array([[x+dx*sx*c+dz*sz*s,y+dy*sy,z-dx*sx*s+dz*sz*c] for dx,dy,dz in [(-.5,-.5,-.5),(.5,-.5,-.5),(.5,.5,-.5),(-.5,.5,-.5),(-.5,-.5,.5),(.5,-.5,.5),(.5,.5,.5),(-.5,.5,.5)]])
  for inds in [[3,2,1,0],[4,5,6,7],[0,1,5,4],[2,3,7,6],[0,4,7,3],[1,2,6,5]]:yield i['material'],f'instance:{number}:{i["feature_id"]}',v[inds],True

def overlap_report(package,tolerance=.02):
 groups=defaultdict(list);duplicates=[];seen={};degenerate=0
 for mat,owner,points,solid in faces(package):
  n=np.cross(points[1]-points[0],points[2]-points[0]);length=np.linalg.norm(n)
  if length<1e-8:degenerate+=1;continue
  n=n/length
  if abs(n[1])>.98:continue # facade validator; ground/roof coverage has its own gate
  key=tuple(sorted(tuple(round(float(x),3) for x in p) for p in points))
  if key in seen:duplicates.append(dict(classification='EXACT_DUPLICATE',a=seen[key],b=owner,material=mat))
  else:seen[key]=owner
  sign=1 if n[np.argmax(abs(n))]>0 else -1;canonical=n*sign;d=float(np.dot(canonical,points[0]));axis=int(np.argmax(abs(canonical)));projected=Polygon(np.delete(points,axis,axis=1)).buffer(0)
  if projected.area<1e-5:continue
  groups[tuple(np.round(canonical,3))].append((d,projected,owner,sign,mat,solid))
 findings=[]
 for entries in groups.values():
  tree=STRtree([e[1] for e in entries])
  for idx,a in enumerate(entries):
   for other in tree.query(a[1]):
    if other<=idx:continue
    b=entries[other];distance=abs(a[0]-b[0])
    if distance>=tolerance or a[2]==b[2]:continue
    overlap=a[1].intersection(b[1]).area
    if overlap<.003:continue
    # Opposing solid faces meet at construction joins; they do not expose two
    # competing fronts. Retain these in the audit instead of silently ignoring.
    classification='INTENTIONAL_OVERLAY' if a[3]!=b[3] else 'COPLANAR' if distance<.001 else 'NEAR_COPLANAR'
    findings.append(dict(classification=classification,a=a[2],b=b[2],separation_m=round(distance,5),overlap_projected_m2=round(overlap,4),materials=[a[4],b[4]]))
 counts=Counter(f['classification'] for f in duplicates+findings)
 return dict(package=package['id'],counts=dict(counts),degenerate_faces=degenerate,findings=duplicates+findings)

def main():
 cat=read('web/public/world/detail/m23/catalog.json')
 if '--baseline' in sys.argv:
  tiles=[read(str(p.relative_to(ROOT))) for p in sorted((ROOT/'data/processed/bgc-tiles').glob('*.json'))]
  volumes=[f for t in tiles for f in t['buildings']];packages=[read('web/public'+e['url']) for e in cat['packages']]
  versions=read('web/package-lock.json')['packages']
  write('data/reports/m23r-baseline.json',dict(branch=command('git','branch','--show-current'),head=command('git','rev-parse','HEAD'),git_status=command('git','status','--short'),node=command('node','--version'),python=sys.version.split()[0],dependencies={k:versions['node_modules/'+k]['version'] for k in ['three','@react-three/fiber','@react-three/drei']},packages=len(packages),landmarks=sum(p['kind']=='landmark' for p in packages),tiles=len(tiles),canonical_buildings=len({f['properties']['canonical_entity_id'] for f in volumes}),render_volumes=len(volumes),signs=sum(len(p['signs']) for p in packages),art=sum(len(p['art']) for p in packages)))
 reports=[overlap_report(read('web/public'+e['url'])) for e in cat['packages'] if e['kind']=='landmark']
 totals=Counter()
 for r in reports:totals.update(r['counts'])
 path='data/reports/m23r-facade-baseline.json' if '--baseline' in sys.argv else 'data/reports/m23r-facade-stability.json'
 write(path,dict(status='PASS' if not any(totals[k] for k in ['EXACT_DUPLICATE','COPLANAR','NEAR_COPLANAR']) else 'FAIL',tolerance_m=.02,scope='Vertical triangles, box faces and sign planes per landmark; opposing construction joins retained as intentional. Animated flicker still requires visual QA.',counts=dict(totals),packages=reports))
 print(path,dict(totals))
if __name__=='__main__':main()
