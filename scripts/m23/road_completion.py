"""Mapped-road detail; placement beyond source geometry is explicitly inferred."""
import math
from shapely.geometry import LineString,Point,Polygon

def road_detail(p,props,g,line,width,paths,buildings):
    tags=props.get('tags',{});lanes=int(tags['lanes']) if str(tags.get('lanes','')).isdigit() else None
    if lanes and 2<=lanes<=8 and width>3:
        for divider in range(1,lanes):
            offset=width*(divider/lanes-.5)
            if abs(offset)<.01:continue # Existing center separator remains authoritative.
            shifted=line.offset_curve(offset)
            for distance in range(6,int(shifted.length)-6,9):
                a=shifted.interpolate(distance);b=shifted.interpolate(distance+3)
                p.surface(LineString([a,b]).buffer(.055,cap_style=2).intersection(g).difference(paths),.071,'PAINT_WHITE','LANE_DIVIDER')
        turns=tags.get('turn:lanes','').split('|')
        if len(turns)==lanes and line.length>24:
            center=line.interpolate(line.length-12);behind=line.interpolate(line.length-14);dx,dy=center.x-behind.x,center.y-behind.y;length=math.hypot(dx,dy)
            if length:
                ux,uy=dx/length,dy/length
                for lane,turn in enumerate(turns):
                    if turn not in ['through','left','right']:continue
                    offset=width*(.5-(lane+.5)/lanes);x,y=center.x-uy*offset,center.y+ux*offset
                    points=[(x-ux*1.6,y-uy*1.6),(x+ux,y+uy)]
                    if turn!='through':sign=1 if turn=='left' else -1;points.append((x+ux-uy*sign,y+uy+ux*sign))
                    shaft=LineString(points).buffer(.11,cap_style=2)
                    tx,ty=points[-1];bx,by=points[-2];size=math.hypot(tx-bx,ty-by);ax,ay=(tx-bx)/size,(ty-by)/size
                    head=Polygon([(tx+ax*.45,ty+ay*.45),(tx-ax*.45-ay*.45,ty-ay*.45+ax*.45),(tx-ax*.45+ay*.45,ty-ay*.45-ax*.45)])
                    p.surface(shaft.union(head).intersection(g).difference(paths),.072,'PAINT_WHITE','TURN_ARROW')
    # Edge markings only on known multi-lane roads; preserve crossing openings.
    if lanes and width>5:
        for offset in [-width/2+.45,width/2-.45]:p.surface(line.offset_curve(offset).buffer(.045).intersection(g).difference(paths.buffer(1)),.071,'PAINT_WHITE','ROAD_EDGE_LINE')
    allowed=['lane','track','opposite_lane','designated']
    sides=[side for side in ['left','right'] if tags.get('cycleway:'+side) in allowed]
    if tags.get('cycleway:both') in allowed:sides=['left','right']
    if not sides and tags.get('cycleway') in allowed:sides=['right']
    for side in sides if width>3 else []:
        track=line.offset_curve((1 if side=='left' else -1)*max(0,width/2-1))
        p.surface(track.buffer(.6).intersection(g).difference(paths),.069,'GLASS_GREEN','BIKE_LANE_PAINTED')
        for distance in range(15,int(track.length)-10,55):
            point=track.interpolate(distance);ahead=track.interpolate(distance+1);yaw=math.atan2(ahead.y-point.y,ahead.x-point.x);ux,uy=math.cos(yaw),math.sin(yaw)
            for shift in [-.55,.55]:
                wheel=Point(point.x+ux*shift,point.y+uy*shift).buffer(.29,resolution=8)
                p.surface(wheel.difference(wheel.buffer(-.055)).intersection(g).difference(paths),.074,'PAINT_WHITE','BIKE_SYMBOL')
            p.surface(LineString([(point.x-ux*.55,point.y-uy*.55),(point.x+uy*.3,point.y-ux*.3),(point.x+ux*.55,point.y+uy*.55)]).buffer(.055).intersection(g).difference(paths),.074,'PAINT_WHITE','BIKE_SYMBOL')
        protected=tags.get('cycleway:'+side)== 'track' or tags.get('cycleway')=='track' or any('cycleway' in k and 'separation' in k and v in ['bollard','flex_post'] for k,v in tags.items())
        if protected:
            for distance in range(8,int(track.length)-8,14):
                q=track.interpolate(distance)
                if not paths.buffer(2).covers(q):p.furniture('BIKE_BOLLARD',q.x,q.y,.07)
    if props.get('class') in ['primary','secondary','tertiary'] and width>4:
        gutter=line.offset_curve(width/2-.14)
        p.surface(gutter.buffer(.12).intersection(g).difference(paths.buffer(1)),.065,'STONE_DARK','GUTTER')
        for distance in range(22,int(gutter.length)-10,65):
            q=gutter.interpolate(distance)
            if not paths.buffer(2).covers(q) and not buildings.buffer(.4).covers(q):p.furniture('STORM_INLET',q.x,q.y,.065)

def crossing_detail(p,g,roads=()):
    rectangle=g.minimum_rotated_rectangle;coords=list(rectangle.exterior.coords)
    a,b=max(zip(coords,coords[1:]),key=lambda ab:math.dist(*ab));dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
    if length<1:return
    ux,uy=dx/length,dy/length;center=g.centroid;half_width=rectangle.area/length/2
    for step in range(math.ceil(length/1.5)):
        offset=-length/2+(step+.5)*1.5;x,y=center.x+ux*offset,center.y+uy*offset
        stripe=Polygon([(x-ux*.32-uy*half_width,y-uy*.32+ux*half_width),(x+ux*.32-uy*half_width,y+uy*.32+ux*half_width),(x+ux*.32+uy*half_width,y+uy*.32-ux*half_width),(x-ux*.32+uy*half_width,y-uy*.32-ux*half_width)])
        p.surface(stripe.intersection(g),.17,'PAINT_WHITE','ZEBRA_CROSSING')
    # Stop bars are inferred from a mapped crossing plus an explicit road lane
    # count. Right-hand approach lanes are selected; unknown lane counts skip.
    from shapely.geometry import shape
    for feature in roads:
        props=feature['properties'];tags=props.get('tags',{});road=shape(feature['geometry'])
        if not road.intersects(g) or not str(tags.get('lanes','')).isdigit() or int(tags['lanes'])<2:continue
        if not props.get('centerline_local'):continue
        line=shape(props['centerline_local']);width=props.get('width_m',0)
        if width<4:continue
        distance=line.project(center);q=line.interpolate(distance);a=line.interpolate(max(0,distance-1));b=line.interpolate(min(line.length,distance+1));size=a.distance(b)
        if size<.1:continue
        vx,vy=(b.x-a.x)/size,(b.y-a.y)/size
        half_cross=max(abs((x-q.x)*vx+(y-q.y)*vy) for x,y in g.exterior.coords)
        for direction in ([1] if tags.get('oneway')=='yes' else [-1] if tags.get('oneway')=='-1' else [-1,1]):
            along=distance-direction*(half_cross+1.5)
            if not 2<along<line.length-2:continue
            origin=line.interpolate(along);rightx,righty=vy*direction,-vx*direction
            lo=-width/2+.5 if tags.get('oneway') in ['yes','-1'] else .25;hi=width/2-.5
            bar=LineString([(origin.x+rightx*lo,origin.y+righty*lo),(origin.x+rightx*hi,origin.y+righty*hi)]).buffer(.2,cap_style=2).intersection(road).difference(g.buffer(.4))
            if bar.area>.3:p.surface(bar,.075,'PAINT_WHITE','CROSSING_STOP_BAR')
