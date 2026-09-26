import importlib.util
import math
import sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/m23'))
from build import Package

def test_facade_rotation_survives_y_up_conversion():
    for yaw in [0,.3,1.2,-.9,math.pi/2]:
        p=Package('fixture');p.block(0,0,0,8,.2,4,yaw=yaw);i=p.instances[0]
        # Three.js Y rotation transforms a local +X point to (cos(a),0,-sin(a)).
        actual=(4*math.cos(i['yaw']),-4*math.sin(i['yaw']))
        assert actual==pytest.approx((4*math.cos(yaw),-4*math.sin(yaw)),abs=2e-5)

def test_constrained_surface_covers_concave_polygon_with_hole():
    from shapely.geometry import Polygon
    p=Package('fixture');shape=Polygon([(0,0),(10,0),(10,3),(5,3),(5,10),(0,10)],holes=[[(1,1),(1,2),(2,2),(2,1)]])
    p.surface(shape,.15,'STONE_LIGHT','test')
    m=p.meshes['STONE_LIGHT'];v=m['vertices'];area=0
    for k in range(0,len(m['indices']),3):
        coords=[(v[i*3],-v[i*3+2]) for i in m['indices'][k:k+3]]
        triangle=Polygon(coords);assert shape.buffer(.001).covers(triangle);area+=triangle.area
    assert area==pytest.approx(shape.area)

def test_thin_roof_parts_have_no_negative_facade_instances():
    from shapely.geometry import box
    from build import facade
    p=Package('fixture');facade(p,box(0,0,10,10),12,12.6,'office')
    assert not p.instances
