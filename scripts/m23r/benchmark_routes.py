"""Derive repeatable, building-free walking routes from retained ground data."""
import json,math
from pathlib import Path
from collections import deque
from shapely.geometry import shape,Point,Polygon,box
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[2]
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def route(mask,seed):
 step=2;x0,y0,x1,y1=mask.bounds
 nodes={(x,y) for x in range(math.floor(x0/step),math.ceil(x1/step)+1) for y in range(math.floor(y0/step),math.ceil(y1/step)+1) if mask.covers(Point(x*step,y*step))}
 start=min(nodes,key=lambda p:math.dist((p[0]*step,p[1]*step),seed))
 def bfs(origin):
  queue=deque([origin]);parent={origin:None};last=origin
  while queue:
   last=queue.popleft()
   for dx,dy in [(1,0),(0,1),(-1,0),(0,-1)]:
    q=(last[0]+dx,last[1]+dy)
    if q in nodes and q not in parent:parent[q]=last;queue.append(q)
  return last,parent
 a,_=bfs(start);b,parent=bfs(a);points=[]
 while b is not None:points.append([b[0]*step,-b[1]*step]);b=parent[b]
 if len(points)<10:raise RuntimeError('Walk route too short')
 return {'points':points,'length_m':(len(points)-1)*step,'method':'2m grid within mapped/constructed walk surfaces, building clearance 0.8m; ping-pong traversal at 7m/s'}
def main():
 buildings=unary_union([shape(f['geometry']) for f in read('data/processed/bgc-buildings.geojson')['features']]).buffer(.8)
 paths=unary_union([shape(f['geometry']) for f in read('data/processed/bgc-paths.geojson')['features'] if f['properties'].get('name')=='Bonifacio High Street'])
 central=read('web/public/world/detail/m23/high_street_central.json')
 terrain=unary_union([Polygon([(v[0],-v[2]) for v in t['points']]) for t in central['terrain']])
 routes={'walk-high-street':route(paths.intersection(box(-350,-100,200,130)).difference(buildings),(-80,15)),
 'walk-central':route(terrain.difference(buildings).difference(Point(-194.783,33.558).buffer(10)),(-194,50))}
 p=ROOT/'web/public/world/detail/m23r/benchmark-routes.json';p.write_text(json.dumps(routes,indent=2)+'\n')
 print({k:v['length_m'] for k,v in routes.items()})
if __name__=='__main__':main()
