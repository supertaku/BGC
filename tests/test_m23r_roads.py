import sys
from pathlib import Path
from shapely.geometry import box,mapping,LineString,Polygon
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/m23'))
from road_completion import crossing_detail,road_detail
from road_evidence import enrich_road_evidence

class Package:
    def __init__(self):self.surfaces=[]
    def surface(self,geometry,height,material,kind):self.surfaces.append((kind,geometry,height))

def road(lanes):
    return dict(geometry=mapping(box(-30,-6,30,6)),properties=dict(tags={'lanes':lanes},width_m=12,centerline_local=mapping(LineString([(-30,0),(30,0)]))))

def test_stop_bars_remain_outside_crossing_and_inside_mapped_road():
    package=Package();crossing=box(-1.5,-6,1.5,6)
    crossing_detail(package,crossing,[road('2')])
    bars=[geometry for kind,geometry,_ in package.surfaces if kind=='CROSSING_STOP_BAR']
    assert len(bars)==2
    assert all(box(-30,-6,30,6).covers(bar) for bar in bars)
    assert all(bar.distance(crossing)>.4 for bar in bars)
    assert bars[0].intersection(bars[1]).is_empty

def test_missing_lane_evidence_does_not_invent_stop_bars():
    package=Package();crossing_detail(package,box(-1.5,-6,1.5,6),[road('')])
    assert not any(kind=='CROSSING_STOP_BAR' for kind,_,_ in package.surfaces)
    assert any(kind=='ZEBRA_CROSSING' for kind,_,_ in package.surfaces)

def test_explicit_left_cycleway_is_on_left_of_source_direction():
    package=Package();line=LineString([(-30,0),(30,0)])
    road_detail(package,dict(tags={'cycleway:left':'lane'}),box(-30,-6,30,6),line,12,Polygon(),Polygon())
    lanes=[g for kind,g,_ in package.surfaces if kind=='BIKE_LANE_PAINTED']
    assert len(lanes)==1 and lanes[0].centroid.y>0

def test_lane_order_follows_left_to_right_source_convention():
    package=Package();line=LineString([(-30,0),(30,0)])
    road_detail(package,dict(tags={'lanes':'2','turn:lanes':'left|right'}),box(-30,-6,30,6),line,12,Polygon(),Polygon())
    arrows=[g for kind,g,_ in package.surfaces if kind=='TURN_ARROW']
    assert len(arrows)==2 and arrows[0].centroid.y>0 and arrows[1].centroid.y<0

def test_original_snapshot_restores_transport_tags_without_mutating_input():
    source=dict(properties=dict(id='osm:way:4940248',tags={'highway':'tertiary'}))
    enriched=enrich_road_evidence([source])[0]
    assert enriched['properties']['tags']['turn:lanes']=='through|through|through|through'
    assert enriched['properties']['tags']['oneway']=='yes'
    assert source['properties']['tags']=={'highway':'tertiary'}

