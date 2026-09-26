"""Evidence-constrained hero ground completion and exact polygon coverage."""
import math
from collections import Counter
from shapely.geometry import shape,box,Point,mapping,Polygon
from shapely.ops import unary_union
from prepare import read,write

def parts(g):
    if g.is_empty:return []
    if g.geom_type=='Polygon':return [g]
    return [p for child in getattr(g,'geoms',[]) for p in parts(child)]

def complete_high_street(package,paths,parks,building_union,road_union,mapped_union):
    named=[shape(f['geometry']) for f in paths if f['properties'].get('name')=='Bonifacio High Street']
    # Estimated hero envelope follows mapped pedestrian geometry, not a claim of
    # surveyed ownership. Every non-building point in this envelope is accounted.
    hero=unary_union(named).buffer(18,join_style=2).intersection(box(-550,-230,260,240))
    usable=hero.difference(building_union);remaining=usable;classes={}
    def take(name,geometry):
        nonlocal remaining
        area=geometry.intersection(remaining);classes[name]=classes.get(name,Polygon()).union(area);remaining=remaining.difference(area)
    take('ROAD',road_union)
    central=read('web/public/world/detail/m23/high_street_central.json')
    water=[]
    mesh=central['meshes'].get('WATER',dict(vertices=[],indices=[]));v=mesh['vertices']
    for i in range(0,len(mesh['indices']),3):water.append(Polygon([(v[k*3],-v[k*3+2]) for k in mesh['indices'][i:i+3]]))
    take('WATER',unary_union(water))
    terrain=unary_union([Polygon([(p[0],-p[2]) for p in t['points']]) for t in central['terrain']])
    def projected(material,predicate):
        mesh=central['meshes'].get(material,dict(vertices=[],indices=[]));vertices=mesh['vertices'];polygons=[]
        for offset in range(0,len(mesh['indices']),3):
            points=[vertices[k*3:k*3+3] for k in mesh['indices'][offset:offset+3]]
            if not predicate([p[1] for p in points]):continue
            polygon=Polygon([(p[0],-p[2]) for p in points])
            if polygon.area>.0001:polygons.append(polygon)
        return unary_union(polygons).intersection(terrain)
    take('LAWN',projected('GRASS',lambda h:min(h)>.3))
    take('STAIRS',projected('STONE_LIGHT',lambda h:min(h)>.3 and max(h)-min(h)<.001))
    take('RAMP',projected('STONE_BEIGE',lambda h:max(h)-min(h)>.02))
    take('PLAZA',terrain)
    take('PEDESTRIAN_PAVING',unary_union([shape(f['geometry']) for f in paths]))
    take('LAWN',unary_union([shape(f['geometry']) for f in parks]))
    fill=remaining
    package.surface(fill,.155,'STONE_BEIGE','HERO_CONNECTING_PAVING',walk=True)
    take('PLAZA',fill)
    # Fine furniture is limited to inferred retail-edge pockets with mapped
    # building, road, existing-object and through-route clearance.
    safe=fill.buffer(-1.8).difference(mapped_union.buffer(1)).difference(road_union.buffer(1.2))
    accepted=[];counts=Counter()
    for patch in parts(safe):
        if patch.area<12:continue
        for n in range(0,int(patch.exterior.length),18):
            point=patch.exterior.interpolate(n);inside=patch.representative_point()
            dx,dy=inside.x-point.x,inside.y-point.y;length=math.hypot(dx,dy)
            if length<.001:continue
            q=Point(point.x+dx/length,point.y+dy/length)
            if not safe.covers(q.buffer(.8)) or any(q.distance(p)<6 for p in accepted):continue
            kind=['BHS_BENCH','BHS_BIN','LIGHT_HIGH_STREET','BHS_PLANTER','TREE_GRATE'][len(accepted)%5]
            package.furniture(kind,q.x,q.y,.155);counts[kind]+=1;accepted.append(q)
            if kind=='BHS_PLANTER':package.tree(q.x,q.y,'PALM_ROYAL',.7);counts['PALM_ROYAL']+=1
    classified=unary_union(list(classes.values()));holes=usable.difference(classified)
    class_area=sum(g.area for g in classes.values());overlap=max(0,class_area-classified.area)
    features=[dict(type='Feature',properties=dict(surface_class=name,grounding='VERIFIED_GEOGRAPHIC' if name in ['ROAD','PEDESTRIAN_PAVING','LAWN'] else 'INFERRED'),geometry=mapping(g)) for name,g in classes.items() if not g.is_empty]
    write('data/visual_reference/m23r-high-street-surfaces.geojson',dict(type='FeatureCollection',features=features,hero_boundary=mapping(hero),boundary_grounding='ESTIMATED'))
    write('data/reports/m23r-public-realm.json',dict(status='PASS' if not [p for p in parts(holes) if p.area>4] else 'FAIL',method='Exact polygon partition, all non-building area within a mapped-path-derived 18m hero envelope',area_m2=usable.area,covered_percent=min(100,classified.area/max(1,usable.area)*100),unknown_percent=holes.area/max(1,usable.area)*100,holes_over_4m2=[mapping(p) for p in parts(holes) if p.area>4],overlap_percent=overlap/max(1,usable.area)*100,classes_m2={k:g.area for k,g in classes.items()},added_connecting_paving_m2=fill.area,added_environment=dict(counts),terrain_note='Elevated grass, flat stair treads and sloping apron are classified from rendered triangle projections. Walk support retains the separate smoothed GroundSampler mesh. Category coverage is not a survey or an accessibility certification.'))

def central_handrails(p,cx,cy,r):
    fid=p.feature('TERRACE_HANDRAILS',sources=['central'],grounding='ESTIMATED',notes='Supplied terrace/ramp photographs support handrails; reconstruction positions and heights estimated.')
    for angle in [0,math.pi]:
        last=None
        for k in range(7):
            rr=r*(.38+.57*k/6);height=.18+1.5*k/6;x,y=cx+math.cos(angle)*rr,cy+math.sin(angle)*rr
            p.block(x,y,height,.075,.075,.9,'METAL_BLACK',fid=fid)
            current=(x,y,height+.9)
            if last:
                a,b=last,current;dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy);nx,ny=-dy/length*.045,dx/length*.045
                vertices=[[x+side*nx,z+up*.045,-(y+side*ny)] for x,y,z in [a,b] for side,up in [(-1,-1),(1,-1),(1,1),(-1,1)]]
                for i,j,k,l in [(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(0,3,2,1),(4,5,6,7)]:p.quad('METAL_BLACK',vertices[i],vertices[j],vertices[k],vertices[l])
            last=current
