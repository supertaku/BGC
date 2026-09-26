"""Compile directory-backed art presence and independently evidenced signs."""
import hashlib,json,math,re,shutil
from pathlib import Path
from collections import Counter
from shapely.geometry import shape,Point
from shapely.ops import unary_union,nearest_points
ROOT=Path(__file__).resolve().parents[2]
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,d):
 p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 cat=read('web/public/world/detail/m23/catalog.json');packages={e['id']:read('web/public'+e['url']) for e in cat['packages']};snapshot=read('data/visual_reference/m23r/directory-snapshot.json')
 buildings=read('data/processed/bgc-buildings.geojson')['features'];parks=read('data/processed/bgc-open-spaces.geojson')['features'];roads=read('data/processed/bgc-roads.geojson')['features'];paths=read('data/processed/bgc-paths.geojson')['features'];walk=unary_union([shape(f['geometry']) for f in paths]);building_union=unary_union([shape(f['geometry']) for f in buildings]);sources={s['source_id']:s for s in read('data/visual_reference/manifest.json')['sources']}
 signs=[];art=[]
 for package in packages.values():
  package['art']=[]
  package['signs']=[s for s in package['signs'] if not s['id'].startswith('m23r-sign:')]
  for sign in package['signs']:
   sign.update(physical_width_m=sign['width_m'],physical_height_m=sign['height_m'],display_text=sign['text'],logo_asset=None,logo_variant=None,source_url=sources.get(sign['source_id'],{}).get('url'),source_type=sources.get(sign['source_id'],{}).get('source_type','MAPPED_NAME'),verified_visible=False,distance_class='PERSISTENT_IDENTITY' if sign['visibility_priority']==1 else 'NEAR_DETAIL',current_as_of=None)
   sign['verification_note']='Mapped building/park name; exact exterior sign presence and placement unverified.'
   signs.append(sign)
 # Photograph 8 supplies visible Mitsukoshi branding. Only the authentic mark
 # region is displayed; the Tokyo store descriptor in the source image is omitted.
 source=ROOT/'data/visual_reference/m23r/assets/mitsukoshi-logo.jpg';target=ROOT/'web/public/world/signage/mitsukoshi-logo.jpg';target.parent.mkdir(parents=True,exist_ok=True)
 if source.exists():
  shutil.copyfile(source,target)
  for sign in packages['mitsukoshi']['signs']:
   sign.update(display_text='MITSUKOSHI',text='MITSUKOSHI',logo_asset='/world/signage/mitsukoshi-logo.jpg',logo_variant='OFFICIAL_MARK_REGION',logo_uv=[0,0,244/466,1],source_url='https://cp.mistore.jp/global/en/nihombashi.html',source_type='OFFICIAL_BRAND_ASSET_AND_USER_PHOTOGRAPH',verified_visible=True,grounding='VERIFIED_VISUAL',rights_status='TRADEMARK_IDENTIFICATION_OFFICIAL_ASSET',verification_note='Exterior mark visible in supplied M23 photos 7/8; anchor dimensions and position estimated. UV framing omits the unrelated Tokyo store descriptor.',physical_width_m=12,physical_height_m=12/(244/44),width_m=12,height_m=12/(244/44))
 logo=ROOT/'data/visual_reference/m23r/assets/uniqlo-logo.png'
 if logo.exists():
  shutil.copyfile(logo,ROOT/'web/public/world/signage/uniqlo-logo.png')
  owner=packages['uniqlo'];b=owner['bounds'];center=Point((b[0]+b[2])/2,-(b[1]+b[3])/2)
  green=unary_union([shape(f['geometry']) for f in parks]).difference(building_union.buffer(.5));point=nearest_points(center,green)[1]
  # Official BGC campaign photo shows lawn branding. Never infer a tenant wall
  # sign from that image, nor claim its temporary installation persists today.
  sign=dict(id='m23r-sign:uniqlo-lawn',building_id='uniqlo',facade='PUBLIC_REALM_CAMPAIGN',position=[round(point.x,3),1.05,round(-point.y,3)],rotation=[0,0,0],width_m=1.5,height_m=.7,physical_width_m=1.5,physical_height_m=.7,sign_type='PUBLIC_REALM_BRAND',text='UNIQLO',display_text='UNIQLO',logo_asset='/world/signage/uniqlo-logo.png',logo_variant='OFFICIAL_BILINGUAL',source_id='uniqlo-official-campaign',source_url='https://www.uniqlo.com/ph/en/special-feature/uniqlo-bgc-high-street',source_type='OFFICIAL_BRAND_PHOTOGRAPH',grounding='VERIFIED_VISUAL',verified_visible=True,current_as_of=None,rights_status='TRADEMARK_IDENTIFICATION_OFFICIAL_ASSET',visibility_priority=3,distance_class='NEAR_DETAIL',verification_note='Official campaign photograph depicts outdoor lawn branding; position estimated and continued physical presence unverified. No exterior storefront placement inferred.')
  packages['high_street']['signs'].append(sign);signs.append(sign)
 records=[r for r in snapshot['records'] if 'see' in r['categories']];placed=[];safe_walk=walk.difference(building_union.buffer(.3))
 zone_names={'Track 30th':'track_30th','Terra 28th':'terra_28th','Kasalikasan':'kasalikasan','Burgos Circle':'burgos_circle','The Mind Museum':'mind_museum_park','JY Campos':'mind_museum_park'}
 for record in records:
  venue=record['venue'] or '';point=None;zone=None;basis='Official directory names a location; exact artwork position is not surveyed.'
  for name,key in zone_names.items():
   if name in venue or name=='Kasalikasan' and record['title']=='Kasalikasan':
    zone=key;b=packages[key]['bounds'];point=Point((b[0]+b[2])/2,-(b[1]+b[3])/2);break
  portal=re.search(r'B:[1-8]',venue)
  if portal:
   found=next((f for f in buildings if f['properties'].get('name')==portal[0]),None)
   if found:point=shape(found['geometry']).centroid;zone='high_street'
  if point is None:
   matches=[f for f in roads if f['properties'].get('name') and f['properties']['name'] in venue]
   geoms=[shape(f['geometry']) for f in matches]
   intersections=[a.intersection(b) for i,a in enumerate(geoms) for b in geoms[i+1:] if a.intersects(b)]
   if intersections:point=unary_union(intersections).centroid
   elif geoms:point=unary_union(geoms).representative_point()
  if point is not None:
   # Neutral information marker goes on a nearby mapped walking surface. This
   # does not assert that the artwork itself occupies the marker's coordinates.
   point=nearest_points(point,safe_walk)[1]
   for attempt in range(8):
    if all(point.distance(p)>2 for p in placed):break
    point=nearest_points(Point(point.x+2.5,point.y+1),safe_walk)[1]
   placed.append(point)
   if zone is None:
    zone=min(packages,key=lambda k:math.hypot((packages[k]['bounds'][0]+packages[k]['bounds'][2])/2-point.x,(packages[k]['bounds'][1]+packages[k]['bounds'][3])/2+point.y))
  item=dict(id='m23r-art:'+record['id'],title=record['title'],artist=record.get('artist'),location=venue,position=[round(point.x,3),.2,round(-point.y,3)] if point else None,rotation=[0,0,0],category='ART_PRESENCE_MARKER',source_url=record['source_url'],source_type='OFFICIAL_BGC_DIRECTORY',source='art',rights_status='NO_ARTWORK_REPRODUCTION',current_status='DIRECTORY_LISTED',current_as_of=snapshot['current_as_of'],geometry_asset=None,texture_asset=None,grounding='ESTIMATED' if point else 'UNKNOWN',notes=basis,representation='NEUTRAL_LOCATION_MARKER' if point else 'DOCUMENTED_PENDING_LOCATION')
  art.append(item)
  if point:packages[zone]['art'].append(item)
 for entry in cat['packages']:
  d=packages[entry['id']];d.pop('content_sha256',None);features=read(f'data/visual_reference/features/{entry["id"]}.json');d['content_sha256']=hashlib.sha256(json.dumps(dict(d,features=features),sort_keys=True).encode()).hexdigest();entry['content_sha256']=d['content_sha256'];entry['signs']=len(d['signs']);entry['art']=len(d['art'])
  path=ROOT/'web/public'/entry['url'].lstrip('/');path.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
 write('web/public/world/detail/m23/catalog.json',cat)
 write('web/public/world/detail/m23r/art-inventory.json',dict(entries=art))
 write('data/reports/m23r-art.json',dict(status='PASS',directory_entries=len(records),accounted_entries=len(art),representations=dict(Counter(a['representation'] for a in art)),works=art))
 write('data/reports/m23r-signage.json',dict(status='PARTIAL_VERIFICATION',anchors=len(signs),verified_visible=sum(s['verified_visible'] for s in signs),official_logos=sum(bool(s['logo_asset']) for s in signs),directory_counts=snapshot['counts'],policy='Directory-only tenants are never placed on exterior facades. Unverified existing building-name labels retain explicit estimated metadata.',signs=signs))
 print('M23R identity',len(signs),'signs',len(art),'art entries',sum(a['position'] is not None for a in art),'markers')
if __name__=='__main__':main()
