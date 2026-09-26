"""Consolidate M23 evidence and entity mappings without changing canonical geography."""
import hashlib
import json
from pathlib import Path
from shapely.geometry import shape, Point

ROOT = Path(__file__).resolve().parents[2]
def read(path): return json.loads((ROOT/path).read_text(encoding='utf-8'))
def write(path, value):
    p=ROOT/path; p.parent.mkdir(parents=True, exist_ok=True)
    content=json.dumps(value,ensure_ascii=False,indent=2)+'\n'
    if not p.exists() or p.read_text(encoding='utf-8') != content: p.write_text(content,encoding='utf-8')

SOURCES = [
 ('bgc','bgc_citywide','https://bgc.com.ph/about-us/','OFFICIAL_OWNER','Walkable mixed-use district and landscaped public spaces.'),
 ('faq','bgc_citywide','https://bgc.com.ph/faqs/','OFFICIAL_OWNER','Internal bus service, dedicated cycling infrastructure and named parks; no exact placements.'),
 ('art','bgc_citywide','https://bgc.com.ph/go/see/','OFFICIAL_OWNER','Current directory snapshot; art is metadata and neutral anchors, not licensed reproductions.'),
 ('track','track_30th','https://bgc.com.ph/directory/track-30th/','OFFICIAL_OWNER','Jogging paths, yoga lawn, meditation gardens, art and designated bicycle parking.'),
 ('central','high_street_central','https://www.crearis.com.ph/bonifacio-high-street-central/','OFFICIAL_ARCHITECT','Amphitheater, interactive water, plaza and gardens; elevations estimated.'),
 ('kasalikasan','kasalikasan','https://www.bgcartscenter.org/installations/kasalikasan','OFFICIAL_OWNER','Living sculpture by Jerusalino V. Araos, circular elevated grass stage, mandala, sandbox, pebble paths.'),
 ('pse','one_bonifacio','https://www.handelarchitects.com/project/philippine-stock-exchange?pagi=residential','OFFICIAL_ARCHITECT','Inflected glass front and deep vertical spine ribs; shared courts.'),
 ('shangri','one_bonifacio','https://www.handelarchitects.com/project/shangri-la-at-the-fort','OFFICIAL_ARCHITECT','Sliding facade volumes, louvers, stone podium, elevated arrival, ramped passage and three bridges.'),
 ('suites','one_bonifacio','https://www.handelarchitects.com/project/the-suites-at-one-bonifacio-high-street?pagi=residential','OFFICIAL_ARCHITECT','Supplied brief: horizontal residential facade expression; page unavailable during retrieval.'),
 ('acpt','acpt','https://www.som.com/projects/arthaland-century-pacific-tower/','OFFICIAL_ARCHITECT','136 m / 32 stories; overlapping glass, clear lobby and roof garden. Verified via indexed official page.'),
 ('museum','mind_museum','https://www.themindmuseum.org/about-us/','OFFICIAL_OWNER','Museum identity. Roof geometry supported by supplied photograph 6.'),
 ('aura_park','sm_aura','https://www.smprime.com/latest_news/sm-auras-sky-park-an-oasis-in-the-heart-of-bustling-global-city/','OFFICIAL_OWNER','Roof garden, water, arched chapel and egg-shaped hall.'),
 ('aura','sm_aura','https://www.smprime.com/company_releases/sm-prime-creates-new-landmark-with-sm-aura-sets-new-standard-in-green-development/','OFFICIAL_OWNER','Three curving ribbons turn upward into tower; staggered northern openings.'),
 ('mitsukoshi','mitsukoshi','https://federalland.ph/news-and-events/in-photos-what-shoppers-can-expect-inside-mitsukoshi-bgc/','OFFICIAL_OWNER','Hemp-leaf-inspired geometric screen above glazed retail base.'),
 ('seasons','mitsukoshi','https://federalland.ph/residential/taguig/the-seasons-residences/','OFFICIAL_OWNER','Four-tower composition over Mitsukoshi podium.'),
 ('uptown','uptown','https://www.megaworldcorp.com/malls/uptown-mall','OFFICIAL_OWNER','Supplied brief: retail podium connecting towers; direct page retrieval unavailable.'),
 ('one_uptown','uptown','https://www.megaworldcorp.com/residences/one-uptown-residence','OFFICIAL_OWNER','Supplied brief: glass/aluminum, landscaped sky gardens and water cascade; retrieval unavailable.'),
 ('parksuites','uptown','https://www.megaworldcorp.com/residences/uptown-parksuites','OFFICIAL_OWNER','Supplied brief: two residential towers, glass/steel and sky lounges; retrieval unavailable.'),
]
TARGETS = [
 ('pse','osm:way:71598335','one_bonifacio','pse'),
 ('suites','osm:way:203910666','one_bonifacio','suites'),
 ('shangri','osm:way:469845356','one_bonifacio','shangri'),
 ('one_bonifacio','osm:way:1078392706','one_bonifacio','retail'),
 ('acpt','osm:way:182331875','acpt','acpt'),
 ('mind_museum','osm:way:183463814','mind_museum','museum'),
 ('sm_aura','osm:way:221590005','sm_aura','aura'),
 ('mitsukoshi','osm:way:1123265838','mitsukoshi','hemp'),
 ('seasons','osm:way:713418274','mitsukoshi','seasons'),
 ('uniqlo','osm:way:443761696','high_street','retail'),
 ('uptown_mall','osm:way:533345980','uptown','retail'),
 ('one_uptown','osm:way:713418275','uptown','sky_garden'),
 ('parksuites','osm:way:538697027','uptown','balcony'),
 ('market_market','osm:way:25006407','market_market','retail'),
 ('serendra_palm','osm:way:27671928','serendra','balcony'),
 ('serendra_mahogany','osm:way:27671996','serendra','balcony'),
 ('serendra_bamboo','osm:way:27672006','serendra','balcony'),
]

def main():
    previous_path=ROOT/'data/visual_reference/manifest.json'
    previous={s['source_id']:s for s in read('data/visual_reference/manifest.json')['sources']} if previous_path.exists() else {}
    sources=[]
    for sid,zone,url,kind,notes in SOURCES:
        sources.append(dict(source_id=sid,entity_id=None,zone=zone,title=sid.replace('_',' ').title(),url=url,source_type=kind,source_domain=url.split('/')[2],viewpoint='Mixed; cardinal orientations not established',use_for=[notes],do_not_infer=['Surveyed dimensions','Unseen facades','Current tenant inventory','Image reuse rights'],confidence='MEDIUM' if 'unavailable' in notes else 'HIGH',retrieved_as_of='2026-09-26',retrieval_status='UNAVAILABLE_SUPPLIED_BRIEF_ONLY' if 'unavailable' in notes else 'VERIFIED_TEXT',rights_status='RESEARCH_ONLY'))
    attachments=[('52feef8f-fa82-4b54-ac0a-4cc23cb3bcea','high_street','Tree rhythm, layered beds, dark planter edges, pale pavers and glazed retail.'),('d69b9698-45ea-49c5-974d-82f422d93968','terra_28th','Lawns, dark paths and play-oriented open space; exact identity inferred.'),('2bef6629-b28c-4b8a-9f6c-583954f9ca67','track_30th','Yellow and plum park sign; paths and benches.'),('b8af1e9d-cb26-4eb2-92b4-77956e3f37e8','kasalikasan','Circular paved clearing, grass terraces and mature canopy; identity inferred.'),('0d1db387-bd8d-4389-8fdc-7b977a78c48e','one_bonifacio','PSE glazed tower, recessed roof, grid and luminous podium band.'),('46dc944f-7c8d-44c8-a8ae-939f070fc339','mind_museum','Swept roof, dark slanting supports, low glazed mass and forecourt.'),('c8f10be8-4dfb-449c-8aab-a95a29af5ba0','mitsukoshi','Repeated geometric screen and tall vertical tower frames.'),('b0dafd6f-0577-4738-a569-0604b0095505','mitsukoshi','Hemp-leaf screen, glazed base, red signage accents; historic construction view.')]
    for n,(key,zone,notes) in enumerate(attachments,1):
        p=Path.home()/f'AppData/Local/Temp/codex-clipboard-{key}.png'
        sources.append(dict(source_id=f'user_photo_{n}',zone=zone,title=f'User supplied photo {n}',source_type='USER_PHOTOGRAPH',source_filename=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else previous.get(f'user_photo_{n}',{}).get('sha256'),grounding='VERIFIED_VISUAL',identity_grounding='INFERRED' if 'inferred' in notes else 'VERIFIED_VISUAL',use_for=[notes],do_not_infer=['Capture date','Unseen views','Measured dimensions'],confidence='MEDIUM',rights_status='RESEARCH_ONLY',retained_image=False))
    sources.append(dict(source_id='osm',title='Pinned normalized OpenStreetMap',source_type='GEOGRAPHIC',url='https://www.openstreetmap.org/copyright',rights_status='ODbL-1.0',grounding='VERIFIED_GEOGRAPHIC'))
    write('data/visual_reference/manifest.json',dict(schema_version=1,grounding_aliases={'VERIFIED_PHOTOGRAPHIC':'VERIFIED_VISUAL'},sources=sources,policy='Research images are not copied to the repository or distributed in runtime assets. Geometry is an estimated interpretation, not a survey.'))
    fs=read('data/processed/bgc-buildings.geojson')['features']; byid={f['properties']['id']:f for f in fs}
    tiles=[read(str(p.relative_to(ROOT))) for p in sorted((ROOT/'data/processed/bgc-tiles').glob('*.json'))]
    targets=[]; claimed=set()
    # Canonical tile ownership already resolves parts, including towers crossing the outline.
    for key,sid,zone,style in TARGETS:
        f=byid[sid]; volumes=[v for t in tiles for v in t['buildings'] if v['properties']['canonical_entity_id']==sid]
        if key=='mitsukoshi': volumes=[v for v in volumes if v['properties']['height_m']<40]
        if key=='acpt': volumes += [v for t in tiles for v in t['buildings'] if v['properties']['id']=='osm:way:538344761']
        if key=='seasons': volumes=[v for t in tiles for v in t['buildings'] if v['properties']['height_m']>=40 and shape(f['geometry']).covers(shape(v['geometry']).representative_point())]
        volumes=[v for v in volumes if v['properties']['id'] not in claimed]
        claimed.update(v['properties']['id'] for v in volumes)
        if not volumes: raise ValueError(f'No resolved geometry: {key}')
        source_key={'sm_aura':'aura','mind_museum':'museum','uptown_mall':'uptown','one_bonifacio':'pse','uniqlo':'user_photo_1','market_market':'osm','serendra_palm':'osm','serendra_mahogany':'osm','serendra_bamboo':'osm'}.get(key,key)
        target=dict(id=key,entity_id=sid,name=f['properties'].get('name') or ('Market! Market!' if key=='market_market' else 'SM Aura Premier'),zone_id=zone,style=style,source_ids=list(dict.fromkeys([source_key,'osm'])),volumes=volumes,grounding='INFERRED',confidence=.65 if source_key!='osm' else .3,rights_status='ORIGINAL_PROCEDURAL_GEOMETRY',modeling_notes='Mapped footprint and part heights; facade dimensions estimated from supplied references or category where only OSM is available.',lifecycle='READY_WITH_GAPS')
        targets.append(target)
    # Explicit scoring, no randomized facade family assignment. Approved seven are excluded.
    entities=read('web/public/world/bgc-interactive.json')['entities']; candidates=[]
    for e in entities:
        if e['detailed_asset_id'] or e['entity_id'] in {t['entity_id'] for t in targets}: continue
        name=e.get('name') or ''; x,z=e['center']; h=e['height_m'] or 0
        if not name or h<35: continue
        factors=dict(visibility=min(5,round(h/45)),named_place=2,height=min(5,round(h/50)),pedestrian_proximity=3 if abs(z)<300 else 1,architectural_uniqueness=0,reference_quality=1,search_importance=2)
        candidates.append(dict(entity_id=e['entity_id'],name=name,factors=factors,score=sum(factors.values()),family='RESIDENTIAL_BALCONY_GRID' if e['building_type'] in ['apartments','residential'] else 'OFFICE_HORIZONTAL_BAND',grounding='INFERRED'))
    candidates.sort(key=lambda c:(-c['score'],c['entity_id']))
    for c in candidates[:14]:
        volumes=[v for t in tiles for v in t['buildings'] if v['properties']['canonical_entity_id']==c['entity_id'] and v['properties']['id'] not in claimed]
        if not volumes: continue
        e=next(e for e in entities if e['entity_id']==c['entity_id']);x,z=e['center']
        zone='uptown' if z<-450 else 'high_street_south' if z>100 else 'forbes_town' if x<-550 else 'office_grid'
        targets.append(dict(id='lite_'+c['entity_id'].split(':')[-1],entity_id=c['entity_id'],name=c['name'],zone_id=zone,style='balcony' if c['family'].startswith('RESIDENTIAL') else 'office',source_ids=['osm'],volumes=volumes,grounding='INFERRED',confidence=.3,rights_status='ORIGINAL_PROCEDURAL_GEOMETRY',modeling_notes='Type-based facade rhythm only; unverified facade detail.',lifecycle='READY_WITH_GAPS'))
        claimed.update(v['properties']['id'] for v in volumes)
    write('data/visual_reference/lod1-lite-candidates.json',dict(factors_policy='Named mapped buildings ranked by exposed factors; architectural uniqueness is zero without reference evidence.',candidates=candidates,selected=[t['entity_id'] for t in targets if t['id'].startswith('lite_')]))
    write('data/visual_reference/targets.json',dict(schema_version=1,targets=targets))
    write('data/visual_reference/height-conflicts.json',dict(conflicts=[dict(entity_id='osm:way:182331875',type='HEIGHT_CONFLICT',height_claims=[dict(value=114.7,source='osm:way:182331875',date='PINNED_SNAPSHOT',confidence=.75,survey_status='UNSURVEYED'),dict(value=136,source='osm:way:538344761',date='PINNED_SNAPSHOT',confidence=.75,survey_status='UNSURVEYED'),dict(value=136,source='acpt',date='2026-09-26',confidence=.95,survey_status='ARCHITECT_PUBLISHED')],resolution='Retain canonical claims. Preview uses mapped 136 m part; no silent source overwrite. Search preview uses maximum part height.')]))
    zones=set(s['zone'] for s in sources if 'zone' in s)|{t['zone_id'] for t in targets}|{'greenway','burgos_circle','de_jesus_oval','terra_28th','high_street_south','serendra','market_market','park_triangle','university_parkway'}
    for zone in sorted(zones):
        write(f'data/visual_reference/zones/{zone}.json',dict(zone_id=zone,source_ids=[s['source_id'] for s in sources if s.get('zone')==zone],lifecycle='READY_WITH_GAPS',coverage={k:('PARTIAL' if k in ['massing','public_realm','landscape','ground_floor'] else 'NONE') for k in ['massing','facade_north','facade_east','facade_south','facade_west','roof','ground_floor','public_realm','landscape','terrain','signage','art','night']},modeling_notes='Cardinal views, measurements and current tenant signs remain unverified; do not invent precision.'))
    print(f'M23 evidence: {len(sources)} sources; {len(targets)} targets; {len(zones)} zones')
if __name__=='__main__': main()
