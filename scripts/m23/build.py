"""Deterministic M23 geometry, shared instance kit and spatial packages.

Run with the repository geospatial Python. Coordinates in output are glTF Y-up.
All dimensions beyond mapped footprints/part heights are explicitly estimated.
"""
import math
import json
import hashlib
from collections import defaultdict, Counter
from shapely.geometry import shape, Point, Polygon, LineString, box
from shapely.ops import unary_union, triangulate, nearest_points
from shapely.geometry.polygon import orient
from shapely.strtree import STRtree
from shapely import constrained_delaunay_triangles, maximum_inscribed_circle
from prepare import ROOT, read, write
from facade_shell import compile_shell
from public_realm_completion import complete_high_street,central_handrails
from road_completion import road_detail,crossing_detail
from road_evidence import enrich_road_evidence
from shangri_completion import complete_shangri,passage_void,arrival_void

MATERIALS={
 'GLASS_BLUE':['#42606e',.3,.15], 'GLASS_NEUTRAL':['#67716f',.36,.12],
 'GLASS_DARK':['#20343a',.25,.12], 'GLASS_GREEN':['#56716b',.34,.1],
 'ALUMINUM_LIGHT':['#b4beb9',.43,.65], 'ALUMINUM_DARK':['#495657',.42,.65],
 'STONE_LIGHT':['#d1cebf',.85,0], 'STONE_BEIGE':['#b6a68c',.85,0],
 'STONE_DARK':['#555851',.9,0], 'CONCRETE_LIGHT':['#b8b9b1',.9,0],
 'CONCRETE_DARK':['#777d76',.9,0], 'BRICK_WARM':['#9b7862',.95,0],
 'WOOD_WARM':['#785b3d',.9,0], 'METAL_BLACK':['#303d3d',.6,.5],
 'SOIL':['#635e46',1,0], 'GRASS':['#668353',1,0], 'LEAF':['#426345',1,0],
 'LEAF_LIGHT':['#799255',1,0], 'WATER':['#567a7b',.16,.4],
 'PAINT_WHITE':['#e1dfca',.92,0], 'PAINT_YELLOW':['#caa840',.9,0],
 'ACCENT_RED':['#a53b37',.8,0], 'TRACK':['#5a6760',.95,0],
 'FLOWER':['#aa7395',.95,0], 'SAND':['#cabb96',1,0]
}

def polys(g):
    if g.is_empty: return []
    if g.geom_type=='Polygon': return [g]
    return [p for child in getattr(g,'geoms',[]) for p in polys(child)]
def xyz(x,y,h): return [round(x,3),round(h,3),round(-y,3)]

class Package:
    def __init__(self,key,kind='zone'):
        self.id=key; self.kind=kind; self.meshes=defaultdict(lambda:dict(vertices=[],indices=[]));self.instances=[];self.features=[];self.signs=[];self.art=[];self.terrain=[];self.bounds=None;self.source='osm';self.ref=[]
    def feature(self,category,sources=None,grounding='INFERRED',notes='Dimensions and positions estimated; no survey claim.'):
        fid=f'{self.id}:{category}:{len(self.features):05d}'
        self.features.append(dict(feature_id=fid,zone_id=self.id,source_ids=sources or [self.source,*self.ref],grounding=grounding,confidence=.45 if grounding in ['INFERRED','ESTIMATED'] else .8,modeling_notes=notes,rights_status='ORIGINAL_PROCEDURAL_GEOMETRY'))
        return fid
    def tri(self,mat,points):
        m=self.meshes[mat];n=len(m['vertices'])//3
        m['vertices'].extend(round(v,6) for p in points for v in p);m['indices'].extend([n,n+1,n+2])
    def quad(self,mat,a,b,c,d): self.tri(mat,[a,b,c]);self.tri(mat,[a,c,d])
    def surface(self,g,h,mat,category,base=None,walk=False):
        fid=self.feature(category)
        for p in polys(g):
            p=orient(p,1)
            for t in constrained_delaunay_triangles(p).geoms:
                coords=list(t.exterior.coords)[:3]; points=[xyz(x,y,h) for x,y in coords]
                self.tri(mat,points)
                if walk:self.terrain.append(dict(points=points,priority=2,feature_id=fid))
            if base is not None:
                for r in [p.exterior,*p.interiors]:
                    cs=list(r.coords)
                    for a,b in zip(cs,cs[1:]):self.quad(mat,xyz(*a,base),xyz(*b,base),xyz(*b,h),xyz(*a,h))
    def inst(self,kind,mat,pos,scale,yaw=0,fid=None):
        self.instances.append(dict(kind=kind,material=mat,position=[round(v,3) for v in pos],scale=[round(v,3) for v in scale],yaw=round(yaw,5),feature_id=fid or self.feature(kind)))
    def block(self,x,y,z,w,d,h,mat='STONE_LIGHT',yaw=0,fid=None):self.inst('box',mat,xyz(x,y,z+h/2),[w,h,d],yaw,fid)
    def beam(self,a,b,width,mat,fid=None):
        # Horizontal line with physical depth. Vertical position is common to both ends.
        dx=b[0]-a[0];dy=b[1]-a[1]; self.block((a[0]+b[0])/2,(a[1]+b[1])/2,a[2],math.hypot(dx,dy),width,width,mat,math.atan2(dy,dx),fid)
    def tree(self,x,y,variant='TREE_LARGE_SPREAD',h=0):
        fid=self.feature(variant); self.block(x,y,h,.35,.35,3.5,'WOOD_WARM',fid=fid)
        if variant=='PALM_ROYAL':
            self.block(x,y,h,.3,.3,7,'STONE_BEIGE',fid=fid)
            for a in range(6):self.inst('sphere','LEAF',xyz(x+1.5*math.cos(a),y+1.5*math.sin(a),h+7),[2.4,.38,.7],-a,fid)
        elif variant=='TREE_COLUMNAR':self.inst('sphere','LEAF',xyz(x,y,h+5),[1.4,3.4,1.4],0,fid)
        else:
            spread=3.8 if variant=='TREE_LARGE_SPREAD' else 2.5 if variant=='TREE_MEDIUM_ROUND' else 1.7
            for a in range(3):
                dx=math.cos(a*2.1)*spread*.42;dy=math.sin(a*2.1)*spread*.42
                self.inst('sphere','FLOWER' if variant=='TREE_FLOWERING' else 'LEAF_LIGHT' if a==1 else 'LEAF',xyz(x+dx,y+dy,h+4.8+a*.2),[spread*.72,1.65,spread*.72],a,fid)
                if variant=='TREE_MULTI_TRUNK':self.block(x+dx*.4,y+dy*.4,h,.22,.22,3.5,'WOOD_WARM',fid=fid)
    def furniture(self,cat,x,y,h=.156,yaw=0):
        fid=self.feature(cat)
        def b(dx,dy,z,w,d,ht,mat):
            c,s=math.cos(yaw),math.sin(yaw); self.block(x+dx*c-dy*s,y+dx*s+dy*c,h+z,w,d,ht,mat,yaw,fid)
        if 'BENCH' in cat:
            b(0,0,.42,2.4,.65,.14,'WOOD_WARM');b(-.85,0,0,.15,.5,.42,'METAL_BLACK');b(.85,0,0,.15,.5,.42,'METAL_BLACK');b(0,-.27,.55,2.4,.1,.4,'WOOD_WARM')
        elif cat.startswith(('SHRUB','TROPICAL','FLOWERING_SHRUB','ORNAMENTAL','GROUNDCOVER','PALM_CLUSTER')):
            self.inst('sphere','FLOWER' if cat=='FLOWERING_SHRUB' else 'LEAF_LIGHT',xyz(x,y,h+.4),[1.2,.6 if 'DENSE' in cat else .35,.8],-yaw,fid)
        elif cat.startswith('LAWN'):
            b(0,0,0,2,2,.025,'GRASS')
        elif cat in ['CURB_STANDARD','CURB_DROP','CURB_ISLAND','GUTTER','STORM_INLET','TREE_GRATE']:
            b(0,0,0,2,.25,.06 if cat in ['CURB_DROP','GUTTER'] else .14,'CONCRETE_LIGHT')
            if cat=='STORM_INLET':b(0,-.14,.015,.65,.03,.08,'METAL_BLACK')
            if cat=='TREE_GRATE':b(0,0,0,1.4,1.4,.035,'METAL_BLACK')
        elif cat.startswith(('RAMP','CURB_RAMP','SLOPE')):
            p0=xyz(x-1,y-2,h);p1=xyz(x+1,y-2,h);p2=xyz(x+1,y+2,h+.25);p3=xyz(x-1,y+2,h+.25);self.quad('STONE_LIGHT',p0,p1,p2,p3)
        elif cat.startswith('STAIR'):
            for k in range(4):b(0,k*.4,0,4,.4,(k+1)*.16,'STONE_LIGHT')
        elif cat in ['ARCADE_SIMPLE','ARCADE_COLUMN','CANOPY_GLASS','CANOPY_METAL','AWNING_RETAIL','SKYWALK_SIMPLE']:
            b(0,0,3.2,5,2.4,.18,'GLASS_NEUTRAL' if cat=='CANOPY_GLASS' else 'STONE_BEIGE')
            if cat in ['ARCADE_SIMPLE','ARCADE_COLUMN','SKYWALK_SIMPLE']:
                b(-2.1,0,0,.3,.3,3.2,'STONE_LIGHT');b(2.1,0,0,.3,.3,3.2,'STONE_LIGHT')
        elif 'LIGHT' in cat or cat=='CCTV_POLE':
            height=3.8 if 'PARK' in cat else 6.5 if 'MAIN' in cat else 4.8
            if 'BOLLARD' in cat:height=.9
            b(0,0,0,.13,.13,height,'ALUMINUM_DARK');b(.45,0,height,1.2,.3,.12,'STONE_LIGHT')
        elif 'PLANTER' in cat:
            b(0,0,0,3,1.3,.5,'STONE_DARK');b(0,0,.5,2.8,1.1,.06,'SOIL');self.inst('sphere','LEAF_LIGHT',xyz(x,y,h+.85),[1.4,.4,.5],-yaw,fid)
        elif cat in ['BIKE_RACK','BHS_BIKE_RACK']:
            for dx in [-.7,0,.7]:b(dx,0,0,.05,.7,.8,'METAL_BLACK');b(dx,0,.8,.08,.7,.08,'METAL_BLACK')
        elif 'BUS' in cat or cat=='COVERED_WALK':
            b(0,0,2.8,5,2.4,.15,'ALUMINUM_LIGHT');b(-2,-.7,0,.13,.13,2.8,'METAL_BLACK');b(2,-.7,0,.13,.13,2.8,'METAL_BLACK');b(0,-.95,.6,4,.06,1.8,'GLASS_NEUTRAL');b(0,0,.5,3,.5,.13,'WOOD_WARM');b(1.8,-.9,.7,.5,.1,1.6,'STONE_LIGHT')
        elif cat in ['TRAFFIC_SIGNAL','PEDESTRIAN_SIGNAL']:
            b(0,0,0,.15,.15,3.5,'METAL_BLACK');b(0,0,2.6,.35,.28,.9,'METAL_BLACK')
            for i,mat in enumerate(['GRASS','PAINT_YELLOW','ACCENT_RED']):b(0,-.16,2.68+i*.25,.16,.05,.16,mat)
        elif cat=='OUTDOOR_DINING':
            b(0,0,.7,1.3,1.3,.12,'WOOD_WARM');b(0,0,0,.1,.1,.7,'METAL_BLACK');b(0,0,0,.06,.06,2.5,'METAL_BLACK');self.inst('cone','STONE_BEIGE',xyz(x,y,h+2.5),[1.6,.45,1.6],-yaw,fid)
            for a in range(4):b(math.cos(a*math.pi/2),math.sin(a*math.pi/2),.4,.45,.45,.12,'WOOD_WARM')
        elif cat=='DRAIN_GRATE':
            b(0,0,0,.6,.4,.015,'METAL_BLACK')
            for i in range(5):b(-.24+i*.12,0,.016,.025,.38,.015,'ALUMINUM_LIGHT')
        elif cat in ['MANHOLE','UTILITY_COVER']:self.inst('cylinder','ALUMINUM_DARK',xyz(x,y,h+.01),[.3,.02,.3],0,fid)
        elif cat=='FIRE_HYDRANT':b(0,0,0,.22,.22,.75,'ACCENT_RED');b(0,0,.5,.65,.18,.18,'ACCENT_RED')
        elif cat in ['UTILITY_CABINET','UTILITY_BOX']:b(0,0,0,.8,.45,1.1,'ALUMINUM_DARK')
        elif cat in ['BOLLARD','BIKE_BOLLARD']:b(0,0,0,.14,.14,.85,'METAL_BLACK')
        elif cat in ['WASTE_BIN','BHS_BIN']:b(0,0,0,.55,.55,.85,'METAL_BLACK');b(0,0,.85,.6,.6,.1,'ALUMINUM_LIGHT')
        elif cat in ['RAILING','GUARDRAIL','ROAD_BARRIER','LANE_SEPARATOR']:b(0,0,.8,2.4,.1,.12,'ALUMINUM_LIGHT');b(-1,0,0,.08,.08,.8,'METAL_BLACK');b(1,0,0,.08,.08,.8,'METAL_BLACK')
        else:b(0,0,0,.1,.1,2.4,'METAL_BLACK');b(0,0,2,.8,.08,.35,'GLASS_GREEN')
    def sign(self,text,x,y,h,width=5,typ='BUILDING_NAME',rotation=0):
        self.signs.append(dict(id=f'{self.id}:sign:{len(self.signs)}',building_id=self.id,facade='ESTIMATED_PRIMARY',position=xyz(x,y,h),rotation=[0,rotation,0],width_m=width,height_m=min(1.8,width*.19),sign_type=typ,text=text,asset=None,source_id=self.ref[0] if self.ref else self.source,grounding='ESTIMATED',current_as_of=None,rights_status='TEXT_ONLY_NO_LOGO',visibility_priority=1 if typ=='BUILDING_NAME' else 3))
    def save(self):
        if self.kind=='landmark':compile_shell(self)
        # Compact indexed geometry. Canonical evidence is retained separately from payloads.
        for m in self.meshes.values():
            vertices=m['vertices'];lookup={};out=[];remap={}
            for i in range(0,len(vertices),3):
                key=tuple(vertices[i:i+3])
                if key not in lookup:lookup[key]=len(out)//3;out.extend(key)
                remap[i//3]=lookup[key]
            m['vertices']=out;m['indices']=[remap[i] for i in m['indices']]
        positions=[i['position'] for i in self.instances]+[[v[j],v[j+1],v[j+2]] for m in self.meshes.values() for v in [m['vertices']] for j in range(0,len(v),3)]
        if positions:self.bounds=[min(p[0] for p in positions),min(p[2] for p in positions),max(p[0] for p in positions),max(p[2] for p in positions)]
        out=dict(schema_version=1,id=self.id,kind=self.kind,bounds=self.bounds,meshes=dict(self.meshes),instances=self.instances,features=self.features,signs=self.signs,art=self.art,terrain=self.terrain,materials=MATERIALS)
        out['content_sha256']=hashlib.sha256(json.dumps(out,sort_keys=True).encode()).hexdigest()
        write(f'data/visual_reference/features/{self.id}.json',self.features)
        out.pop('features')
        path=ROOT/f'web/public/world/detail/m23/{self.id}.json';path.parent.mkdir(parents=True,exist_ok=True)
        content=json.dumps(out,ensure_ascii=False,separators=(',',':'))+'\n'
        if not path.exists() or path.read_text(encoding='utf-8')!=content:path.write_text(content,encoding='utf-8')
        return dict(id=self.id,kind=self.kind,bounds=self.bounds,url=f'/world/detail/m23/{self.id}.json',feature_count=len(self.features),instances=len(self.instances),mesh_triangles=sum(len(m['indices'])//3 for m in self.meshes.values()),signs=len(self.signs),content_sha256=out['content_sha256'])

def edges(g):
    for p in polys(g):
        cs=list(orient(p,1).exterior.coords)
        for a,b in zip(cs,cs[1:]):
            dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
            if length>2:yield a,b,length,math.atan2(dy,dx),(dy/length,-dx/length)

def facade(pkg,g,base,top,style):
    if top-base<5:return # Thin mapped roof/parapet parts have no occupied facade.
    glass='GLASS_GREEN' if style=='seasons' else 'GLASS_NEUTRAL' if style in ['balcony','suites'] else 'GLASS_BLUE'
    for a,b,length,yaw,(nx,ny) in edges(g.simplify(.45)):
        cx,cy=(a[0]+b[0])/2,(a[1]+b[1])/2
        fid=pkg.feature('CURTAIN_WALL' if top>40 else 'PODIUM_GLAZING')
        # Glazing is a separate physical skin, clear of the mapped structural shell.
        pkg.block(cx+nx*.25,cy+ny*.25,base+.6,length,.2,top-base-1.2,glass,yaw,fid)
        interval=3.6 if style in ['balcony','suites'] else 5.8
        for h in range(math.ceil((base+4)/interval),math.floor(top/interval)):
            depth=.85 if style in ['balcony','suites'] else .3
            pkg.block(cx+nx*(.4+depth/2),cy+ny*(.4+depth/2),h*interval,length,depth,.22 if depth<.8 else .32,'STONE_LIGHT' if style in ['balcony','suites'] else 'ALUMINUM_DARK',yaw,fid)
        spacing=5.5 if style in ['pse','shangri','seasons'] else 9
        for k in range(1,int(length/spacing)):
            t=k/max(1,int(length/spacing)); x=a[0]+(b[0]-a[0])*t;y=a[1]+(b[1]-a[1])*t
            pkg.block(x+nx*.4,y+ny*.4,base+3,.22 if style!='seasons' else .65,.9 if style in ['pse','shangri'] else .25,top-base-4,'STONE_BEIGE' if style=='seasons' else 'ALUMINUM_LIGHT',yaw,fid)
        if top<40 and base<1 and length>12:
            pkg.block(cx+nx*1.2,cy+ny*1.2,4.3,length*.82,2.8,.22,'STONE_BEIGE',yaw,fid)
            for k in range(1,int(length/7)):
                t=k/int(length/7);pkg.block(a[0]+(b[0]-a[0])*t+nx*.24,a[1]+(b[1]-a[1])*t+ny*.24,.3,.13,.28,4,'ALUMINUM_LIGHT',yaw,fid)

def roof_shell(pkg,g,base,rise,mat='ALUMINUM_LIGHT'):
    xmin,ymin,xmax,ymax=g.bounds;cx,cy=g.centroid.coords[0];w=xmax-xmin;d=ymax-ymin
    # Clipped curved surface, avoiding a rectangular slab outside the actual footprint.
    def height(x,y):
        u=(x-xmin)/w;v=(y-ymin)/d
        # Swept crest and a downturned long edge frame the open forecourt.
        return base+rise*math.sin(math.pi*min(1,max(0,v)))*.8+rise*.5*(1-u)-5*max(0,(u-.8)/.2)**2
    for i in range(16):
        for j in range(24):
            cell=box(xmin+w*i/16,ymin+d*j/24,xmin+w*(i+1)/16,ymin+d*(j+1)/24).intersection(g)
            for p in polys(cell):
                for t in constrained_delaunay_triangles(p).geoms:
                    pkg.tri(mat,[xyz(x,y,height(x,y)) for x,y in list(t.exterior.coords)[:3]])
    for a,b,_,_,_ in edges(g):pkg.quad(mat,xyz(*a,height(*a)),xyz(*b,height(*b)),xyz(*b,height(*b)-1.2),xyz(*a,height(*a)-1.2))
    pkg.feature('CURVED_ROOF',grounding='ESTIMATED',notes='Photograph-supported swept silhouette; roof curvature and dimensions estimated.')
    return height

def landmark(t):
    p=Package(t['id'],'landmark');p.ref=t['source_ids'];style=t['style']
    for f in t['volumes']:
        props=f['properties'];p.source=props['id'];g=shape(f['geometry']);base=props.get('min_height_m',0);top=props['height_m']
        if top<=base:continue
        if style=='shangri' and top<35:
            g=g.difference(passage_void()).difference(arrival_void())
        if style=='museum':
            xmin,ymin,xmax,ymax=g.bounds
            body=g.buffer(-3).intersection(box(xmin,ymin+24,xmax-15,ymax))
            p.surface(body,7.7,'GLASS_DARK','LOW_ASYMMETRIC_BODY',base=.16)
            for h in [3.6,7.1]:p.surface(body.buffer(.4).difference(body.buffer(-.3)),h,'ALUMINUM_DARK','GLAZING_BAND',base=h-.45)
            roof_height=roof_shell(p,g,8.4,6.8)
            for a,b,length,yaw,n in edges(g):
                if length>20:
                    for fraction in [.2,.75]:
                        x=a[0]+(b[0]-a[0])*fraction-n[0]*2;y=a[1]+(b[1]-a[1])*fraction-n[1]*2
                        # Slanted solid support, represented as a sheared box mesh.
                        corners=[xyz(x+dx,y+dy,.16) for dx,dy in [(-.8,-.9),(.8,-.9),(.8,.9),(-.8,.9)]]
                        corners += [xyz(x+dx-n[0]*2.2,y+dy-n[1]*2.2,roof_height(x+dx-n[0]*2.2,y+dy-n[1]*2.2)-.15) for dx,dy in [(-.8,-.9),(.8,-.9),(.8,.9),(-.8,.9)]]
                        for a0,b0,c0,d0 in [(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)]:p.quad('METAL_BLACK',corners[a0],corners[b0],corners[c0],corners[d0])
            continue
        p.surface(g,top,'GLASS_NEUTRAL' if top>45 else 'STONE_BEIGE','MAPPED_MASSING',base=base)
        facade(p,g,base,top,style)
        if style=='hemp':
            # Sparse lattice is real geometry with depth, never an unlicensed photo texture.
            for a,b,length,yaw,(nx,ny) in edges(g.simplify(1)):
                if length<18:continue
                ux,uy=(b[0]-a[0])/length,(b[1]-a[1])/length
                fid=p.feature('HEMP_SCREEN',notes='Simplified geometric hemp-leaf rhythm from photographs 7/8; module scale estimated.')
                for k in range(int(length/2.4)):
                    x=a[0]+ux*(k+.5)*2.4+nx*.55;y=a[1]+uy*(k+.5)*2.4+ny*.55
                    for z in [5.3,7.4,9.5]:
                        # Six spokes per cell: clipped triangle lattice rendered as slender boxes.
                        center=xyz(x,y,z)
                        for angle in [0,math.pi/3,2*math.pi/3]:
                            dz=math.sin(angle)*1.4;du=math.cos(angle)*1.4
                            v1=xyz(x-ux*du,y-uy*du,z-dz);v2=xyz(x+ux*du,y+uy*du,z+dz)
                            # Thin ribbon with real projection off glass.
                            # Width lies in the facade plane, not perpendicular to it.
                            side=[-ux*math.sin(angle)*.07,math.cos(angle)*.07,uy*math.sin(angle)*.07]
                            p.quad('STONE_LIGHT',[v1[j]+side[j] for j in range(3)],[v2[j]+side[j] for j in range(3)],[v2[j]-side[j] for j in range(3)],[v1[j]-side[j] for j in range(3)])
                p.block((a[0]+b[0])/2+nx*.4,(a[1]+b[1])/2+ny*.4,top-.4,length,.8,.4,'STONE_LIGHT',yaw)
                for split in range(0,int(length),24):
                    p.block(a[0]+ux*split+nx*.5,a[1]+uy*split+ny*.5,4.5,1.6,.9,top-4.5,'STONE_BEIGE',yaw)
        if style=='acpt' and top>120:
            for band in range(3):p.surface(g.buffer(-2-band*.4).difference(g.buffer(-3.4-band*.4)),top-3+band*.8,'GRASS','ROOF_GARDEN')
        if style=='sky_garden' and top>60:
            for level in [.35,.65,.85]:p.surface(g.buffer(.3).difference(g.buffer(-1.5)),top*level,'GRASS','SKY_GARDEN_VOID')
        if style=='aura' and top<40:
            for offset in [0,2.3,4.6]:
                ring=g.buffer(-offset).difference(g.buffer(-offset-1.25));p.surface(ring,top+offset*.32,'STONE_LIGHT','CURVILINEAR_RIBBON',base=top-1.4+offset*.32)
            garden=g.buffer(-8);p.surface(garden,top+.18,'GRASS','ROOF_GARDEN')
            cx,cy=g.representative_point().coords[0]
            p.inst('sphere','ALUMINUM_LIGHT',xyz(cx+15,cy+18,top+5),[15,8,11])
            # Open-ended tubular chapel shell; roof-only external interpretation.
            for k in range(20):
                a=k*math.pi/20;b=(k+1)*math.pi/20
                p.quad('STONE_LIGHT',xyz(cx-16+7*math.cos(a),cy-28,top+.4+7*math.sin(a)),xyz(cx-16+7*math.cos(a),cy-2,top+.4+7*math.sin(a)),xyz(cx-16+7*math.cos(b),cy-2,top+.4+7*math.sin(b)),xyz(cx-16+7*math.cos(b),cy-28,top+.4+7*math.sin(b)))
            for off in [-18,0,18]:p.inst('sphere','GLASS_NEUTRAL',xyz(cx+off,cy+42,top+1.5),[4,2.5,3])
        if style=='aura' and top>100:
            # Attach ribbons to a real mapped facade edge, not its axis-aligned bounds.
            podium=unary_union([shape(v['geometry']) for v in t['volumes'] if v['properties']['height_m']<40])
            edge_a,edge_b,length,yaw,(nx,ny)=min((e for e in edges(g) if e[2]>12),key=lambda e:Point((e[0][0]+e[1][0])/2,(e[0][1]+e[1][1])/2).distance(podium.centroid))
            ux,uy=(edge_b[0]-edge_a[0])/length,(edge_b[1]-edge_a[1])/length
            ribbon_width=length*.28
            for i in range(3):
                x=edge_a[0]+ux*length*(i+.5)/3+nx*.4;y=edge_a[1]+uy*length*(i+.5)/3+ny*.4;zmax=top-i*3
                p.block(x,y,23,ribbon_width,1.2,zmax-23,'STONE_LIGHT',yaw)
                for k in range(10):
                    a=k*math.pi/20;b=(k+1)*math.pi/20
                    da=14*(1-math.cos(a));za=23-7*math.sin(a)
                    db=14*(1-math.cos(b));zb=23-7*math.sin(b)
                    half=ribbon_width/2
                    p.quad('STONE_LIGHT',xyz(x-ux*half+nx*da,y-uy*half+ny*da,za),xyz(x+ux*half+nx*da,y+uy*half+ny*da,za),xyz(x+ux*half+nx*db,y+uy*half+ny*db,zb),xyz(x-ux*half+nx*db,y-uy*half+ny*db,zb))
        if style=='shangri' and top<40:
            for a,b,length,yaw,(nx,ny) in edges(g):
                cx,cy=(a[0]+b[0])/2,(a[1]+b[1])/2
                p.block(cx+nx*.3,cy+ny*.3,6,length,.5,top-6,'STONE_BEIGE',yaw)
                p.block(cx+nx*.4,cy+ny*.4,.2,length,.6,1.2,'STONE_DARK',yaw)
        if style in ['pse','seasons','shangri'] and top>100:
            p.surface(g.buffer(.4).difference(g.buffer(-.6)),top+.8,'ALUMINUM_DARK','CROWN',base=top)
    g=unary_union([shape(v['geometry']) for v in t['volumes']]);x,y=g.centroid.coords[0]
    if style=='shangri':complete_shangri(p,t)
    edges_front=list(edges(g));a,b,l,yaw,n=max(edges_front,key=lambda e:e[2]);cx,cy=(a[0]+b[0])/2+n[0],(a[1]+b[1])/2+n[1]
    p.sign(t['name'],cx,cy,5.2,min(15,l*.65),rotation=math.atan2(n[0],-n[1]))
    if style=='pse':p.block(cx,cy,6.6,min(l,32),.3,1.4,'PAINT_WHITE',yaw);p.sign('PSE',cx+n[0]*.2,cy+n[1]*.2,7.3,5,rotation=math.atan2(n[0],-n[1]))
    return p

PARKS={'Track 30th':'track_30th','Terra 28th':'terra_28th','Kasalikasan':'kasalikasan','De Jesus Oval':'de_jesus_oval','BGC Greenway Park':'greenway','Burgos Circle Park':'burgos_circle','J.Y. Campos Park':'mind_museum_park','BHS Central':'high_street_central'}

def street_packages(paths,roads,buildings,pois,bu,ru):
    tilepkgs={};world=read('web/public/world/bgc-world.json')
    def tilepkg(x,y):
        t=next((t for t in world['tiles'] if box(*t['bounds']).covers(Point(x,y))),None)
        if not t:return None
        key='street_'+t['tile_id'];return tilepkgs.setdefault(key,Package(key))
    path_geoms=[shape(f['geometry']) for f in paths];building_geoms=[shape(f['geometry']) for f in buildings]
    path_tree=STRtree(path_geoms);building_tree=STRtree(building_geoms)
    for road_index,f in enumerate(roads):
        props=f['properties'];tags=props.get('tags',{});g=shape(f['geometry']);line=props.get('centerline_local');width=props.get('width_m',0)
        if not line or not g.intersects(box(-950,-750,850,1150)):continue
        line=shape(line);q=line.interpolate(.5,normalized=True);p=tilepkg(q.x,q.y)
        if not p:continue
        near_path=unary_union([path_geoms[int(i)] for i in path_tree.query(g.buffer(2))])
        near_build=unary_union([building_geoms[int(i)] for i in building_tree.query(g.buffer(2))])
        p.source=props['id'];p.ref=['faq']
        road_detail(p,props,g,line,width,near_path,near_build)
        if tags.get('lanes') and str(tags['lanes']).isdigit() and int(tags['lanes'])>=2:
            for s in range(6,int(line.length)-6,9):
                a=line.interpolate(s);b=line.interpolate(min(s+3,line.length));stripe=LineString([a,b]).buffer(.06,cap_style=2).intersection(g).difference(near_path)
                p.surface(stripe,.068,'PAINT_WHITE','LANE_LINE')
        # Curbs stop at mapped pedestrian crossings to preserve traversable entries.
        if props.get('class') in ['primary','secondary','tertiary','residential'] and line.length>20:
            edge=g.boundary.buffer(.10).difference(near_path.buffer(1.5)).difference(near_build.buffer(.2))
            p.surface(edge,.18,'CONCRETE_LIGHT','CURB_STANDARD',base=.06)
    for f in pois:
        props=f['properties'];category=props['category'];g=shape(f['geometry']);x,y=g.x,g.y
        if not box(-950,-750,850,1150).covers(g):continue
        kind={'bicycle_parking':'BIKE_RACK','outdoor_seating':'OUTDOOR_DINING','bus_station':'BGC_BUS_STOP_STANDARD','bicycle_repair_station':'UTILITY_CABINET'}.get(category)
        if not kind or bu.buffer(.3).covers(g) or ru.covers(g):continue
        p=tilepkg(x,y)
        if p:p.source=props['id'];p.furniture(kind,x,y)
    # Raw mapped transport/utility nodes omitted by the older environment sidecar.
    from pyproj import Transformer
    transform=Transformer.from_crs(4326,32651,always_xy=True);ox,oy=transform.transform(121.050972,14.550806)
    raw=read('data/raw/osm/bgc-2026-09-14T162150Z.json')
    building_clearance=bu.buffer(.4);road_boundary=ru.boundary
    for node in raw.get('elements',[]):
        if node['type']!='node' or 'lat' not in node:continue
        tags=node.get('tags',{});kind=None
        if tags.get('highway')=='traffic_signals':kind='TRAFFIC_SIGNAL'
        elif tags.get('highway')=='bus_stop':kind='BGC_BUS_STOP_COMPACT'
        elif tags.get('emergency')=='fire_hydrant':kind='FIRE_HYDRANT'
        elif tags.get('man_made')=='street_cabinet':kind='UTILITY_CABINET'
        elif tags.get('man_made')=='manhole':kind='MANHOLE'
        elif tags.get('man_made')=='surveillance':kind='CCTV_POLE'
        if not kind:continue
        gx,gy=transform.transform(node['lon'],node['lat']);x,y=gx-ox,gy-oy
        if not box(-950,-750,850,1150).covers(Point(x,y)):continue
        # Signal nodes describe an intersection, not a pole survey. Move the inferred
        # pole to the nearest clear edge; never install a post in the traffic lane.
        if kind in ['TRAFFIC_SIGNAL','BGC_BUS_STOP_COMPACT'] and ru.covers(Point(x,y)):
            edge=nearest_points(Point(x,y),road_boundary)[1];dx,dy=edge.x-x,edge.y-y;length=math.hypot(dx,dy)
            if length<.01:continue
            x,y=edge.x+dx/length*.55,edge.y+dy/length*.55
        if building_clearance.covers(Point(x,y)):continue
        p=tilepkg(x,y)
        if p:p.source=f"osm:node:{node['id']}";p.ref=['faq'];p.furniture(kind,x,y)
    # Mapped crossing surfaces have priority over roads.
    for f in paths:
        if f['properties'].get('tags',{}).get('crossing')!='zebra':continue
        g=shape(f['geometry']);c=g.centroid;p=tilepkg(c.x,c.y)
        if not p:continue
        p.source=f['properties']['id'];xmin,ymin,xmax,ymax=g.bounds
        crossing_detail(p,g,[road for road in roads if shape(road['geometry']).intersects(g)])
    return [p.save() for p in tilepkgs.values() if p.features]

def main():
    targets=read('data/visual_reference/targets.json')['targets']; entries=[]
    for t in targets:
        p=landmark(t); entry=p.save();entry.update(entity_id=t['entity_id'],name=t['name'],replaces=[v['properties']['id'] for v in t['volumes']],replacement_entity_ids=sorted({v['properties']['canonical_entity_id'] for v in t['volumes']}),identity_visibility='OWNER_TILE',height_m=max(v['properties']['height_m'] for v in t['volumes']),activation_m=260 if not t['id'].startswith('lite_') else 200);entries.append(entry)
    paths=read('data/processed/bgc-paths.geojson')['features'];roads=read('data/processed/bgc-roads.geojson')['features'];buildings=read('data/processed/bgc-buildings.geojson')['features'];parks=read('data/processed/bgc-open-spaces.geojson')['features'];pois=read('data/processed/bgc-pois.geojson')['features']
    roads=enrich_road_evidence(roads)
    bu=unary_union([shape(f['geometry']) for f in buildings]);ru=unary_union([shape(f['geometry']) for f in roads]);pu=unary_union([shape(f['geometry']) for f in paths]); mapped=[shape(f['geometry']) for f in pois if f['properties']['category'] in ['tree','bench','bollard','waste_basket','street_lamp','shelter']]
    obstacles=bu.buffer(.7).union(ru.buffer(.3)).union(pu.buffer(.4)); mapped_union=unary_union(mapped).buffer(3)
    for f in parks:
        name=f['properties'].get('name')
        if name not in PARKS:continue
        key=PARKS[name];p=Package(key);p.source=f['properties']['id'];p.ref=[{'track_30th':'track','high_street_central':'central','kasalikasan':'kasalikasan'}.get(key,'faq')];g=shape(f['geometry']);center=g.representative_point();cx,cy=center.coords[0];safe=g.buffer(-3).difference(obstacles).difference(mapped_union);xmin,ymin,xmax,ymax=g.bounds
        p.surface(g.difference(bu).difference(pu),.113,'GRASS','LAWN_CARABAO' if key=='kasalikasan' else 'LAWN_SHORT')
        local_paths=[path for path in paths if shape(path['geometry']).intersects(g)]
        pg=unary_union([shape(path['geometry']) for path in local_paths]).intersection(g.buffer(-.5)).difference(bu)
        if pg.area>1:
            p.ref += [path['properties']['id'] for path in local_paths]
            p.surface(pg,.163,'TRACK' if key=='track_30th' else 'STONE_BEIGE','RUNNING_PATH' if key=='track_30th' else 'PEBBLE_PATH' if key=='kasalikasan' else 'PARK_PATH')
        p.source=f['properties']['id']
        if key=='high_street_central':
            # Raise the terraced ring above existing ground; center and outer rim meet base.
            clear_circle=maximum_inscribed_circle(g.difference(bu.buffer(.8)),tolerance=.2)
            cx,cy=clear_circle.coords[0]
            r=min(25,max(3,clear_circle.length-5.1)); fid=p.feature('AMPHITHEATER',grounding='ESTIMATED',notes='Crearis confirms amphitheater. Estimated center selected inside largest mapped building-free circle; levels, radii and gradients are not surveyed.')
            terrain_extent=Point(cx,cy).buffer(r+5).intersection(g).difference(bu)
            for step in range(6):
                inner=r*.38+step*r*.095;outer=inner+r*.095
                ring=Point(cx,cy).buffer(outer,quad_segs=16).difference(Point(cx,cy).buffer(inner,quad_segs=16)).intersection(terrain_extent)
                lawn=ring.intersection(box(cx-r,cy+2,cx+r,cy+r)) if step>1 else Polygon()
                p.surface(ring.difference(lawn),.18+(step+1)*.25,'STONE_LIGHT','STAIR_PLAZA_WIDE',base=.16)
                if not lawn.is_empty:p.surface(lawn,.18+(step+1)*.25,'GRASS','GRASS_TERRACE',base=.16)
            # Exact smooth walk support uses matching vertices, including boundary descent.
            rings=[(0,.163),(r*.38,.18),(r*.95,1.68),(r+5,.163)]
            for (ra,ha),(rb,hb) in zip(rings,rings[1:]):
                for k in range(64):
                    aa=k*math.tau/64;ab=(k+1)*math.tau/64
                    coords=[(cx+ra*math.cos(aa),cy+ra*math.sin(aa),ha),(cx+rb*math.cos(aa),cy+rb*math.sin(aa),hb),(cx+rb*math.cos(ab),cy+rb*math.sin(ab),hb),(cx+ra*math.cos(ab),cy+ra*math.sin(ab),ha)]
                    for inds in [(0,1,2),(0,2,3)]:
                        tri=[coords[i] for i in inds]
                        if Polygon([(a,b) for a,b,h in tri]).area<.001:continue
                        if not terrain_extent.buffer(.005).covers(Polygon([(a,b) for a,b,h in tri])):continue
                        pts=[xyz(a,b,h) for a,b,h in tri];p.terrain.append(dict(points=pts,priority=2,feature_id=fid))
                        if ra>=r*.95 or ra==0:p.tri('STONE_BEIGE',[[v[0],v[1]+.012,v[2]] for v in pts])
                        # The continuous outer apron provides the grade transition;
                        # no diagonal plane cuts across the concentric seating.
            water=Point(cx,cy).buffer(r*.2,quad_segs=12);p.surface(water,.178,'WATER','WATER_PLAZA')
            central_handrails(p,cx,cy,r)
            for i in range(8):p.inst('cylinder','ALUMINUM_DARK',xyz(cx+math.cos(i*math.tau/8)*r*.23,cy+math.sin(i*math.tau/8)*r*.23,.185),[.08,.03,.08])
            safe=safe.difference(terrain_extent.buffer(2))
        elif key=='kasalikasan':
            r=min(17,(xmax-xmin)*.25,(ymax-ymin)*.25);circle=Point(cx,cy).buffer(r,quad_segs=24)
            p.surface(circle,.19,'BRICK_WARM','MANDALA_CENTER',base=.11,walk=True)
            for step in range(3):p.surface(Point(cx,cy).buffer(r+2+step*1.5).difference(Point(cx,cy).buffer(r+step*1.5)).intersection(g),.35+step*.22,'GRASS','ELEVATED_GRASS_STAGE',base=.11,walk=True)
            p.surface(Point(cx+r*.7,cy-r*.7).buffer(2.5).intersection(g),.22,'SAND','SANDBOX')
            safe=safe.difference(circle.buffer(6))
        elif key=='terra_28th':
            # Colored play pads are inference, not reproductions of protected artwork.
            for i in range(3):
                pad=box(cx-9+i*7,cy-3,cx-4+i*7,cy+3).intersection(safe)
                p.surface(pad,.12,['PAINT_YELLOW','ACCENT_RED','GLASS_BLUE'][i],'PLAY_LAWN_ACCENT')
        step=13 if key in ['greenway','de_jesus_oval','kasalikasan'] else 19
        accepted=[]
        for ix in range(math.floor(xmin/step),math.ceil(xmax/step)):
            for iy in range(math.floor(ymin/step),math.ceil(ymax/step)):
                digest=hashlib.sha256(f'{key}:{ix}:{iy}'.encode()).digest();x=ix*step+(digest[0]/255-.5)*3;y=iy*step+(digest[1]/255-.5)*3
                if not safe.covers(Point(x,y).buffer(2.3)):continue
                p.tree(x,y,'TREE_MULTI_TRUNK' if key=='kasalikasan' else 'TREE_LARGE_SPREAD' if key in ['greenway','de_jesus_oval','terra_28th'] else 'TREE_MEDIUM_ROUND')
                accepted.append(Point(x,y))
                if digest[2]<120:p.inst('sphere','LEAF_LIGHT',xyz(x+1.8,y,.6),[1.6,.55,1.3])
        for i in range(1,int(g.length//26)):
            q=g.exterior.interpolate(i*26) if g.geom_type=='Polygon' else g.boundary.interpolate(i*26);inside=LineString([q,center]).interpolate(2.5)
            if not safe.covers(inside.buffer(1.5)) or any(inside.distance(t)<4 for t in accepted):continue
            p.furniture('LIGHT_PARK_PATH' if i%3==0 else 'BENCH',inside.x,inside.y)
        q=g.boundary.interpolate(g.length*.2);p.sign(name,q.x,q.y,1.8,4,'PARK_SIGN')
        if key in ['track_30th','terra_28th','kasalikasan','mind_museum_park','burgos_circle']:
            art={'track_30th':('Larong Pinoy','Ang Gerilya'),'terra_28th':('Color Me Chameleon','Rico Lascano'),'kasalikasan':('Kasalikasan','Jerusalino V. Araos'),'mind_museum_park':("People’s Minds",'Lor Calma'),'burgos_circle':('The Trees','Reynato Paz Contreras')}[key]
            p.art.append(dict(id=key+':art',title=art[0],artist=art[1],location=name,position=xyz(cx,cy,.2),rotation=[0,0,0],category='LOCATION_ANCHOR',source='art',rights_status='RESEARCH_ONLY',current_status='DIRECTORY_LISTED_2026_09_26',geometry_asset=None,texture_asset=None,grounding='ESTIMATED',notes='Anchor identifies approximate zone only; no artwork reproduction.'))
        entry=p.save()
        if key=='high_street_central':entry.update(focus=xyz(cx,cy,1),walk_position=xyz(cx+r*.7,cy,2))
        entries.append(entry)
    # High Street paving, retail-edge rhythm and planted perimeter detail.
    p=Package('high_street');p.ref=['bgc','user_photo_1'];core=box(-550,-230,260,240)
    planted_spine=box(-230,-80,230,80)
    for f in parks:
        g=shape(f['geometry']).intersection(planted_spine).difference(obstacles).difference(mapped_union)
        if g.area<25:continue
        p.source=f['properties']['id'];p.surface(g,.116,'GRASS','HIGH_STREET_LAWN')
        for poly in polys(g):
            safe=poly.buffer(-2.3)
            for d in range(0,int(poly.length),16):
                q=poly.exterior.interpolate(d);q=LineString([q,poly.representative_point()]).interpolate(3)
                if safe.covers(q):p.tree(q.x,q.y,'TREE_LARGE_SPREAD');p.inst('sphere','LEAF_LIGHT',xyz(q.x+1,q.y,.55),[1.3,.5,.8])
    for f in paths:
        if f['properties'].get('name')!='Bonifacio High Street':continue
        g=shape(f['geometry']).intersection(core).difference(bu);p.source=f['properties']['id']
        if g.area<10:continue
        p.surface(g,.16,'STONE_LIGHT','HIGH_STREET_MAIN_PAVER')
        p.surface(g.difference(g.buffer(-.6)),.167,'STONE_DARK','HIGH_STREET_EDGE_PAVER')
        for poly in polys(g):
            xmin,ymin,xmax,ymax=poly.bounds
            for x in range(math.floor(xmin/5)*5,math.ceil(xmax/5)*5,5):p.surface(box(x,ymin,x+.16,ymax).intersection(poly),.17,'CONCRETE_DARK','PAVER_JOINT')
            safe=poly.difference(poly.buffer(-3.2)).difference(bu.buffer(.6)).difference(ru.buffer(.4)).difference(mapped_union)
            others=unary_union([shape(q['geometry']) for q in paths if q['properties']['id']!=p.source]);safe=safe.difference(others.buffer(.4))
            for i in range(1,int(poly.length//22)):
                q=poly.exterior.interpolate(i*22);dest=LineString([q,poly.representative_point()]).interpolate(1.5)
                if safe.covers(dest.buffer(1.4)):p.furniture(['BHS_PLANTER','BHS_BENCH','LIGHT_HIGH_STREET'][i%3],dest.x,dest.y)
    # Selected low retail edges already in the mapped High Street spine.
    for f in buildings:
        g=shape(f['geometry']);props=f['properties']
        if props.get('name') not in ['B:1','B:2','B:3','B:4','B:5','B:6','B:7','B:8','C1','C2','C3']:continue
        p.source=props['id'];facade(p,g,0,min(props['height_m'],16),'retail')
    for title,artist in [('Bearable Lightness','Reg Yuson and Ronald Achacoso'),('Hearsay','Reg Yuson')]:p.art.append(dict(id='high-street:'+title,title=title,artist=artist,location='Bonifacio High Street portal',position=None,rotation=[0,0,0],category='LOCATION_ANCHOR',source='art',rights_status='RESEARCH_ONLY',current_status='DIRECTORY_LISTED_2026_09_26',geometry_asset=None,texture_asset=None,grounding='UNKNOWN'))
    complete_high_street(p,paths,parks,bu,ru,mapped_union)
    entries.append(p.save())
    # Shared One Bonifacio public-realm package from mapped paths between its volumes.
    p=Package('one_bonifacio_realm');p.ref=['pse','shangri','user_photo_1'];extent=box(-558,8,-363,242)
    courts=pu.intersection(extent).difference(bu)
    p.surface(courts,.175,'STONE_LIGHT','SHARED_COURTS')
    # Local estimated raised terrace with a continuous boundary-to-base transition.
    court_polys=polys(courts)
    if court_polys:
        terrace=max(court_polys,key=lambda g:g.area);fid=p.feature('ELEVATED_PLAZA_RAMP',notes='Architect confirms multilevel public realm; this local transition is estimated, not surveyed.')
        xmin,ymin,xmax,ymax=terrace.bounds
        for x in range(math.floor(xmin),math.ceil(xmax),4):
            for y in range(math.floor(ymin),math.ceil(ymax),4):
                for part in polys(box(x,y,x+4,y+4).intersection(terrace)):
                    for tri in constrained_delaunay_triangles(part).geoms:
                        points=[xyz(a,b,.18+min(1,terrace.boundary.distance(Point(a,b))/8)*1.5) for a,b in list(tri.exterior.coords)[:3]]
                        p.tri('STONE_BEIGE',points);p.terrain.append(dict(points=points,priority=2,feature_id=fid))
    for f in pois:
        q=shape(f['geometry']);cat=f['properties']['category']
        if extent.covers(q) and cat=='fountain':p.source=f['properties']['id'];p.surface(q.buffer(3).difference(bu),.20,'WATER','ARRIVAL_FOUNTAIN')
    entries.append(p.save())
    # Tile-owned streetscape, using actual per-road evidence; no uniform markings.
    for zone,road_name in [('forbes_town','Forbes Town Road'),('university_parkway','University Parkway'),('mckinley_parkway','McKinley Parkway')]:
        selected=[f for f in roads if f['properties'].get('name')==road_name]
        if not selected:continue
        p=Package(zone);p.ref=['faq'];p.source=selected[0]['properties']['id']
        corridor=unary_union([shape(f['geometry']) for f in selected]).buffer(12)
        p.surface(pu.intersection(corridor).difference(bu),.176,'STONE_BEIGE','DISTRICT_SIDEWALK')
        for f in parks:
            g=shape(f['geometry']).intersection(corridor).difference(bu).difference(pu)
            if g.area>10:p.source=f['properties']['id'];p.surface(g,.12,'GRASS','LANDSCAPED_EDGE')
        entries.append(p.save())
    # A reviewable reusable kit gallery is generated separately and never loaded in the city.
    kit=Package('city_kit','fixture');kit.ref=['faq'];kit.source='osm'
    kit_types=['ROAD_MAIN','ROAD_SECONDARY','ROAD_SERVICE','ROAD_DROP_OFF','ROAD_PARKING_EDGE','BIKE_LANE_PAINTED','BIKE_LANE_PROTECTED','BIKE_BOLLARD','BIKE_RACK','CURB_STANDARD','CURB_DROP','CURB_RAMP','CURB_ISLAND','GUTTER','DRAIN_GRATE','STORM_INLET','TRAFFIC_SIGNAL','PEDESTRIAN_SIGNAL','STREET_NAME_SIGN','DIRECTION_SIGN','PARKING_SIGN','BOLLARD','ROAD_BARRIER','LANE_SEPARATOR','MANHOLE','UTILITY_COVER','FIRE_HYDRANT','UTILITY_CABINET','CCTV_POLE','SECURITY_OBJECT','BGC_BUS_STOP_STANDARD','BGC_BUS_STOP_COMPACT','BGC_BUS_STOP_SIGN','ARCADE_SIMPLE','ARCADE_COLUMN','CANOPY_GLASS','CANOPY_METAL','AWNING_RETAIL','COVERED_WALK','SKYWALK_SIMPLE','BENCH','PLANTER','WASTE_BIN','TREE_GRATE','RAILING','GUARDRAIL','LAWN_SHORT','LAWN_CARABAO','SHRUB_LOW','SHRUB_DENSE','TROPICAL_FOLIAGE','FLOWERING_SHRUB','PALM_CLUSTER','ORNAMENTAL_GRASS','GROUNDCOVER','LIGHT_MAIN_STREET','LIGHT_SECONDARY','LIGHT_HIGH_STREET','LIGHT_PARK_PATH','LIGHT_PLAZA','LIGHT_BOLLARD','STAIR_PLAZA_WIDE','STAIR_LANDSCAPE','STAIR_ENTRY','RAMP_ACCESSIBLE','RAMP_PLAZA','SLOPE_LANDSCAPE']
    for i,kind in enumerate(kit_types):
        x,y=(i%10)*10,(i//10)*10
        if kind.startswith(('ROAD_','BIKE_LANE')):
            kit.block(x,y,0,6,4,.06,'STONE_DARK');kit.block(x,y,.065,.12,3,.01,'PAINT_WHITE')
            if kind=='BIKE_LANE_PROTECTED':kit.furniture('BIKE_BOLLARD',x+2,y)
        else:kit.furniture(kind,x,y)
    for i,kind in enumerate(['TREE_SMALL_ROUND','TREE_MEDIUM_ROUND','TREE_LARGE_SPREAD','TREE_COLUMNAR','TREE_FLOWERING','PALM_ROYAL','TREE_MULTI_TRUNK']):kit.tree(i*12,-15,kind)
    for f in kit.features:f['grounding']='PROCEDURAL';f['modeling_notes']='Reusable category fixture; no claim of site placement or exact visual design.'
    kit.save();write('data/visual_reference/city-kit.json',dict(categories=kit_types,facade_primitives=['WINDOW_GRID','CURTAIN_WALL','HORIZONTAL_BAND','VERTICAL_FIN','LOUVER_SCREEN','BALCONY_STACK','STONE_PANEL','METAL_PANEL','PODIUM_GLAZING','CANOPY','ROOF_SCREEN','SKY_GARDEN_VOID'],placement_policy='Instantiate only with local mapped or photographic evidence; unplaced fixtures are not city features.'))
    entries.extend(street_packages(paths,roads,buildings,pois,bu,ru))
    entries.sort(key=lambda e:e['id'])
    write('web/public/world/detail/m23/catalog.json',dict(schema_version=1,status='AWAITING_USER_TEST',default_enabled=False,coordinate_frame='metres; east/up/-north',packages=entries,materials=MATERIALS,source_manifest='data/visual_reference/manifest.json'))
    write('data/reports/m23-zone-status.json',dict(status='READY_FOR_VISUAL_QA',zones=entries))
    print(f'M23 compiled {len(entries)} packages; {sum(e["instances"] for e in entries)} primitive instances')

if __name__=='__main__':main()
