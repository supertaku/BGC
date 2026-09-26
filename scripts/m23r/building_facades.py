"""Attach canonical-ID-seeded facade parameters to existing merged GLBs.

No architectural measurements are inferred from the generated facade rhythm.
Original positions, indices, tile metadata and approved replacement groups remain.
"""
import hashlib,json,struct
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
from shapely.geometry import shape,Point
ROOT=Path(__file__).resolve().parents[2]
FAMILIES=['OFFICE_CURTAIN_BLUE','OFFICE_CURTAIN_NEUTRAL','OFFICE_VERTICAL_FIN','OFFICE_HORIZONTAL_BAND','OFFICE_STONE_GLASS',
 'RESIDENTIAL_BALCONY','RESIDENTIAL_GLASS_BALCONY','RESIDENTIAL_LIGHT_WINDOW','RESIDENTIAL_PODIUM_TOWER',
 'RETAIL_GLAZED','RETAIL_STONE','RETAIL_OPEN_FRONT','PARKING_LOUVER','PARKING_SCREEN','CIVIC_STONE','CIVIC_GLASS','CIVIC_CONCRETE','RESIDENTIAL_DARK_WINDOW']
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,d):
 p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def classify(props):
 tags=props.get('tags',{});kind=tags.get('building','');name=(props.get('name') or '').lower()
 if kind in ['apartments','residential','house','dormitory','terrace']:category='RESIDENTIAL'
 elif kind=='hotel' or 'hotel' in name:category='HOTEL'
 elif kind=='parking' or tags.get('amenity')=='parking':category='PARKING'
 elif kind in ['school','university','college'] or tags.get('amenity') in ['school','university','college']:category='EDUCATIONAL'
 elif kind in ['hospital','clinic'] or tags.get('amenity') in ['hospital','clinic']:category='MEDICAL'
 elif kind in ['warehouse','industrial','service','shed']:category='INDUSTRIAL_SERVICE'
 elif kind in ['civic','government','church','cathedral','public','museum']:category='CIVIC'
 elif kind=='office':category='OFFICE'
 elif kind in ['retail','kiosk','supermarket']:category='RETAIL'
 elif kind in ['commercial','mixed_use']:category='MIXED_USE'
 else:category='UNKNOWN'
 seed=int(hashlib.sha256(props['canonical_entity_id'].encode()).hexdigest()[:8],16)
 choices={'OFFICE':range(5),'RESIDENTIAL':[5,6,7,8,17],'HOTEL':[1,4,7,8],'PARKING':[12,13],'EDUCATIONAL':[14,15,16],
 'MEDICAL':[1,14,15],'INDUSTRIAL_SERVICE':[12,16],'CIVIC':[14,15,16],'RETAIL':[9,10,11],'MIXED_USE':[4,8,9],
 'UNKNOWN':range(5) if props['height_m']>45 else [7,9,10,14,16]}[category]
 family=choices[seed%len(choices)]
 return dict(entity_id=props['canonical_entity_id'],category=category,family=FAMILIES[family],family_index=family,seed=seed,grounding='PROCEDURAL',classification_grounding='INFERRED',source_ids=props.get('source_ids',[props['id']]))
def accessor(doc,blob,index):
 a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];components={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]
 return np.ndarray((a['count'],components),dtype=dtype,buffer=blob,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',np.dtype(dtype).itemsize*components),np.dtype(dtype).itemsize)).copy()
def patch_glb(path,features,records):
 content=path.read_bytes();size=struct.unpack_from('<I',content,12)[0];doc=json.loads(content[20:20+size]);offset=20+size;length=struct.unpack_from('<I',content,offset)[0];blob=bytearray(content[offset+8:offset+8+length]);lookup=defaultdict(list)
 for f in features:
  props=f['properties'];base=props.get('min_height_m',0);top=props['height_m']
  if top<=base:continue
  geom=shape(f['geometry']);polygons=[geom] if geom.geom_type=='Polygon' else list(geom.geoms)
  for p in polygons:
   for ring in [p.exterior,*p.interiors]:
    for x,y in ring.coords:
     for z in [base,top]:lookup[(round(x,3),round(z,3),round(-y,3))].append(props)
 generic_material=len(doc.get('materials',[]));doc.setdefault('materials',[]).append(dict(name='BGC_UNIVERSAL_FACADE',doubleSided=False,pbrMetallicRoughness=dict(baseColorFactor=[1,1,1,1],metallicFactor=.08,roughnessFactor=.58)))
 assigned=set();unmatched=[];ambiguous=0
 def append_accessor(values,kind,component=5126,target=34962):
  while len(blob)%4:blob.append(0)
  binary=np.array(values,dtype='<f4' if component==5126 else '<u4').tobytes();view=len(doc['bufferViews']);doc['bufferViews'].append(dict(buffer=0,byteOffset=len(blob),byteLength=len(binary),target=target));blob.extend(binary)
  index=len(doc['accessors']);doc['accessors'].append(dict(bufferView=view,componentType=component,count=len(values),type=kind));return index
 shapes={f['properties']['id']:shape(f['geometry']) for f in features}
 for node in doc['nodes']:
  if 'mesh' not in node or '_buildings_' not in node.get('name',''):continue
  allowed=set(json.loads(node.get('extras',{}).get('entity_ids','[]')))
  for primitive in doc['meshes'][node['mesh']]['primitives']:
   positions=accessor(doc,blob,primitive['attributes']['POSITION']);normals=accessor(doc,blob,primitive['attributes']['NORMAL']);indices=accessor(doc,blob,primitive['indices']).ravel();parameters=[];candidates=[]
   for position in positions:
    matches=[p for p in lookup.get(tuple(round(float(x),3) for x in position),[]) if p['canonical_entity_id'] in allowed]
    if not matches:
     unmatched.append([float(x) for x in position]);continue
    candidates.append(matches)
    if len({p['canonical_entity_id'] for p in matches})>1:ambiguous+=1
   if len(candidates)!=len(positions):raise ValueError(f'{path.name}: unmatched exported building vertices {unmatched[:3]}')
   outpos=[];outnorm=[];outindices=[];remap={}
   for t in range(0,len(indices),3):
    tri=indices[t:t+3];ids=set.intersection(*[{p['id'] for p in candidates[i]} for i in tri]);choices=[p for p in candidates[tri[0]] if p['id'] in ids]
    if not choices:raise ValueError(f'{path.name}: triangle without common source volume')
    center=positions[tri].mean(axis=0)-normals[tri].mean(axis=0)*.005;point=Point(float(center[0]),float(-center[2]))
    choices.sort(key=lambda p:(not shapes[p['id']].buffer(.001).covers(point),shapes[p['id']].area,p['canonical_entity_id'],p['id']))
    props=choices[0];identity=props['canonical_entity_id'];record=records[identity];assigned.add(identity)
    for i in tri:
     key=(int(i),props['id'])
     if key not in remap:
      remap[key]=len(outpos);outpos.append(positions[i]);outnorm.append(normals[i]);parameters.append([record['family_index'],record['seed']%65521/65521,props.get('min_height_m',0),props['height_m']])
     outindices.append(remap[key])
   primitive['attributes']['POSITION']=append_accessor(outpos,'VEC3');primitive['attributes']['NORMAL']=append_accessor(outnorm,'VEC3');primitive['indices']=append_accessor(outindices,'SCALAR',5125,34963)
   primitive['attributes']['_BGC_FACADE']=append_accessor(parameters,'VEC4');primitive['material']=generic_material
  node.setdefault('extras',{})['facade_grounding']='PROCEDURAL_CANONICAL_ID_SEEDED'
 # Compact away superseded accessors instead of shipping two copies of geometry.
 packed=bytearray();new_accessors=[];new_views=[];remapped={}
 for mesh in doc['meshes']:
  for primitive in mesh['primitives']:
   for semantic,index in [*primitive['attributes'].items(),('indices',primitive['indices'])]:
    if index not in remapped:
     a=dict(doc['accessors'][index]);values=accessor(doc,blob,index);binary=values.tobytes()
     while len(packed)%4:packed.append(0)
     a['bufferView']=len(new_views);a.pop('byteOffset',None)
     if semantic=='POSITION':a['min']=values.min(axis=0).tolist();a['max']=values.max(axis=0).tolist()
     new_views.append(dict(buffer=0,byteOffset=len(packed),byteLength=len(binary),target=34963 if semantic=='indices' else 34962));packed.extend(binary);remapped[index]=len(new_accessors);new_accessors.append(a)
    if semantic=='indices':primitive['indices']=remapped[index]
    else:primitive['attributes'][semantic]=remapped[index]
 blob=packed;doc['bufferViews']=new_views;doc['accessors']=new_accessors
 doc['buffers'][0]['byteLength']=len(blob);encoded=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();encoded+=b' '*((-len(encoded))%4);blob+=b'\0'*((-len(blob))%4)
 result=struct.pack('<III',0x46546c67,2,12+8+len(encoded)+8+len(blob))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(blob),0x004e4942)+blob
 return result,assigned,ambiguous
def main():
 sources=sorted((ROOT/'data/processed/bgc-tiles').glob('*.json'));tiles=[json.loads(p.read_text(encoding='utf-8')) for p in sources];records={}
 for tile in tiles:
  for f in tile['buildings']:
   props=f['properties'];identity=props['canonical_entity_id']
   # Canonical record chosen independently of render-volume ordering.
   if identity not in records:records[identity]=classify(props)
 original=read('web/public/world/detail/m23/tile-variants.json');variants={};coverage=set();ambiguous=0
 for tile in tiles:
  key=tile['tile_id'];variant=original['tiles'].get(key)
  path=ROOT/'web/public'/variant['url'].lstrip('/') if variant else ROOT/f'exports/bgc/tiles/{key}.glb'
  result,assigned,count=patch_glb(path,tile['buildings'],records);coverage.update(assigned);ambiguous+=count
  output=ROOT/f'web/public/models/m23r/tiles/{key}.glb';output.parent.mkdir(parents=True,exist_ok=True)
  if not output.exists() or output.read_bytes()!=result:output.write_bytes(result)
  variants[key]=dict(url=f'/models/m23r/tiles/{key}.glb',size_bytes=len(result),sha256=hashlib.sha256(result).hexdigest())
 missing=sorted(set(records)-coverage);aliases={}
 features=[f for tile in tiles for f in tile['buildings']]
 for identity in missing:
  a=next(f for f in features if f['properties']['canonical_entity_id']==identity)
  for b in features:
   owner=b['properties']['canonical_entity_id']
   if owner in coverage and a['properties']['height_m']==b['properties']['height_m'] and shape(a['geometry']).equals(shape(b['geometry'])):
    aliases[identity]=owner;break
 missing=[i for i in missing if i not in aliases]
 write('web/public/world/detail/m23r/tile-variants.json',dict(schema_version=1,tiles=variants))
 write('data/reports/m23r-building-coverage.json',dict(status='PASS' if not missing else 'FAIL',canonical_buildings=len(records),covered_buildings=len(coverage)+len(aliases),coincident_source_aliases=aliases,missing=missing,tiles=len(tiles),categories=dict(Counter(r['category'] for r in records.values())),families=dict(Counter(r['family'] for r in records.values())),shared_boundary_vertex_ambiguities=ambiguous,grounding='All generated facade designs are procedural filler; underlying footprints/heights retain source grounding.',records=sorted(records.values(),key=lambda r:r['entity_id'])))
 print(f'M23R facades: {len(coverage)}/{len(records)} canonical buildings; {len(variants)} tiles; ambiguities={ambiguous}')
 if missing:raise SystemExit(1)
if __name__=='__main__':main()
