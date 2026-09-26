"""Deterministic inferred placement policies in source east/north metres."""
import json
import math
from collections import Counter
from pathlib import Path
from shapely.geometry import Point, shape, box
from shapely.affinity import rotate, translate
from shapely.ops import unary_union
ROOT = Path(__file__).resolve().parents[2]
HEIGHTS = json.loads((ROOT / 'data/config/surface-heights.json').read_text())
POLICY = {
 'grounding': 'INFERRED', 'inset': {'BENCH_LINEAR':1.2,'PLANTER_RECT':1.5,'LIGHT_POLE_STANDARD':.7},
 'radius': {'TREE_CLUSTER':2.2,'BENCH_LINEAR':1.05,'PLANTER_RECT':1.52,'LIGHT_POLE_STANDARD':.2},
 'spacing': {'TREE_CLUSTER':7,'BENCH_LINEAR':10,'PLANTER_RECT':5,'LIGHT_POLE_STANDARD':12},
 'mapped_radius': {'TREE_GENERIC':2.5,'BENCH_GENERIC':1.5,'STREET_LAMP_GENERIC':.5,'BOLLARD_GENERIC':.3,'WASTE_BIN_GENERIC':.5,'SHELTER_GENERIC':2.1},
 'same_type_clearance': {'TREE_CLUSTER':4.5,'BENCH_LINEAR':3,'LIGHT_POLE_STANDARD':3.5},
 'building_buffer':.5,'walkway_buffer':.3,'tree_grid':14,'boundary_interval':22,
 'paving_width':.55,'park_edge_width':.65,'plaza_edge_strip':3.2,'tree_grid_jitter':4,'park_inset':3.5,
}
MATCH = {'TREE_CLUSTER':'TREE_GENERIC','BENCH_LINEAR':'BENCH_GENERIC','LIGHT_POLE_STANDARD':'STREET_LAMP_GENERIC'}
def load_features(name):
 return json.loads((ROOT / f'data/processed/bgc-{name}.geojson').read_text())['features']
def boundary_frame(poly, distance, inset):
 edge=poly.exterior
 a=edge.interpolate((distance-.1)%edge.length); b=edge.interpolate((distance+.1)%edge.length)
 dx,dy=b.x-a.x,b.y-a.y; length=math.hypot(dx,dy)
 if length < 1e-8: return None
 tx,ty=dx/length,dy/length; p=edge.interpolate(distance)
 for nx,ny in ((-ty,tx),(ty,-tx)):
  if poly.contains(Point(p.x+nx*.05,p.y+ny*.05)):
   return Point(p.x+nx*inset,p.y+ny*inset),math.atan2(ty,tx)
 return None
class Context:
 def __init__(self):
  self.paths=load_features('paths'); self.roads=load_features('roads'); self.buildings=load_features('buildings')
  self.path=unary_union([shape(f['geometry']) for f in self.paths])
  self.road=unary_union([shape(f['geometry']) for f in self.roads])
  self.building=unary_union([shape(f['geometry']) for f in self.buildings]).buffer(POLICY['building_buffer'])
  self.open=unary_union([shape(f['geometry']) for f in load_features('open-spaces')])
  self.owner_path_masks={}
  self.environment={}
  for file in sorted((ROOT/'web/public/world/tiles').glob('*.json')):
   for category,items in json.loads(file.read_text()).get('environment',{}).items():
    for item in items: self.environment[item['id']]=(category,Point(item['position'][0],-item['position'][1]))
  self.counts={'paths':len(self.paths),'roads':len(self.roads),'buildings':len(self.buildings),'mapped':dict(Counter(c for c,p in self.environment.values()))}
 def base(self,point):
  for name,geom in [('PATH',self.path),('OPEN_SPACE',self.open),('ROAD',self.road)]:
   if geom.covers(point): return name
  return 'GROUND'
 def rejection(self,item,polygon,accepted):
  cat=item['category']; p=Point(item['position'][0],-item['position'][1]); radius=POLICY['radius'][cat]
  footprint=p.buffer(radius)
  if cat in ("BENCH_LINEAR","PLANTER_RECT"):
   length,width = (2,.6) if cat=="BENCH_LINEAR" else (2.8,1.15)
   footprint=translate(rotate(box(-length/2,-width/2,length/2,width/2), item["yaw_rad"], use_radians=True),p.x,p.y)
  if not polygon.covers(footprint): return 'outside_owner'
  if footprint.intersects(self.building): return 'building'
  if footprint.intersects(self.road): return 'road'
  # Plaza furniture may occupy the owner's edge strip, never its through-route core.
  if item['placement_rule']=='PARK_GRID': paths=self.path
  else:
   if item['source_id'] not in self.owner_path_masks:
    self.owner_path_masks[item['source_id']]=unary_union([shape(f['geometry']) for f in self.paths if f['properties']['id'] != item['source_id']])
   paths=self.owner_path_masks[item['source_id']]
  if footprint.intersects(paths.buffer(POLICY['walkway_buffer'])): return 'walkway'
  if item['placement_rule']=='BOUNDARY_INSET' and footprint.intersects(polygon.buffer(-POLICY['plaza_edge_strip'])): return 'walkway'
  for mapped,p2 in self.environment.values():
   clearance=radius+POLICY['mapped_radius'].get(mapped,1)
   if MATCH.get(cat)==mapped: clearance=max(clearance,POLICY['same_type_clearance'][cat])
   if p.distance(p2)<clearance: return 'existing_object'
  for other in accepted:
   c2=other['category']; minimum=radius+POLICY['radius'][c2]
   if c2==cat: minimum=max(minimum,POLICY['spacing'][cat])
   if {cat,c2}=={'BENCH_LINEAR','PLANTER_RECT'}: minimum=max(minimum,3)
   if p.distance(Point(other['position'][0],-other['position'][1]))<minimum: return 'spacing'
  return None
