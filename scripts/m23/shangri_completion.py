"""Architect-supported elements; dimensions and siting remain estimated."""
from shapely.geometry import Point,box,shape,LineString

def passage_void():return box(-468,181,-436,198)
def arrival_void():return Point(-482,158).buffer(7.5,resolution=20)

def complete_shangri(p,target):
    tower=shape(target['volumes'][0]['geometry']);ballroom=shape(target['volumes'][2]['geometry'])
    y=193.;line=LineString([(-550,y),(-380,y)]);left=tower.intersection(line).bounds[2];right=ballroom.intersection(line).bounds[0]
    width=right-left
    if width>2:
        fid=p.feature('THREE_GLASS_BRIDGES',sources=['shangri'],grounding='ESTIMATED',notes='Handel text confirms three glass bridges; architect photograph 00.731.11.019 shows vertically separated glazed links. Levels, widths and placement fitted approximately to mapped podium volumes.')
        for base in [9.4,15.1,20.8]:
            p.block((left+right)/2,y,base,width+1,4.2,.32,'STONE_LIGHT',fid=fid)
            p.block((left+right)/2,y,base+3.4,width+1,4.2,.25,'ALUMINUM_LIGHT',fid=fid)
            for dy in [-2.1,2.1]:
                p.block((left+right)/2,y+dy,base+.32,width,.12,3.08,'GLASS_GREEN',fid=fid)
                for k in range(1,int(width/2.6)):
                    p.block(left+k*width/max(1,int(width/2.6)),y+dy,base+.32,.09,.16,3.08,'ALUMINUM_LIGHT',fid=fid)
    court=arrival_void();p.surface(court,3.6,'STONE_DARK','ELEVATED_ARRIVAL_DROPOFF',base=.18,walk=True)
    # Keep the arrival court outside every retained tall-volume footprint.
    for volume in target['volumes']:
        if volume['properties']['height_m']>35 and court.intersection(shape(volume['geometry'])).area>.001:raise ValueError('Arrival court intersects a retained tower')
    fountain=Point(-482,159).buffer(2,resolution=16);p.surface(fountain,3.8,'WATER','ARRIVAL_FOUNTAIN')
    p.surface(fountain.buffer(.45).difference(fountain),3.88,'STONE_LIGHT','FOUNTAIN_EDGE',base=3.6)
    for x,y in [(-488,157),(-487,163),(-477,163),(-475.5,157)]:p.tree(x,y,'PALM_ROYAL',3.6)
    # Broad, openly estimated graded approach meets both the flat path and court.
    fid=p.feature('RAMPED_ARRIVAL_PASSAGE',sources=['shangri'],grounding='ESTIMATED',notes='Open raised drop-off/passage confirmed by architect; approach gradient is a reconstruction estimate.')
    points=[[-485,.18,-138],[-479,.18,-138],[-479,3.6,-151.5],[-485,3.6,-151.5]]
    p.quad('STONE_BEIGE',*points)
    for indices in [(0,1,2),(0,2,3)]:p.terrain.append(dict(points=[points[i] for i in indices],priority=3,feature_id=fid))
