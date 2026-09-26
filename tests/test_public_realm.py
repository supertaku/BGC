"""Targeted M21R/M22R contracts, coordinate sign and placement rejection tests."""
import sys
import unittest
from pathlib import Path
from shapely.geometry import box, Point
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/visual_detail'))
from placement import Context, boundary_frame, HEIGHTS, POLICY
class PublicRealmTests(unittest.TestCase):
 def test_height_hierarchy(self):
  self.assertLess(HEIGHTS['ROAD_TOP'],HEIGHTS['OPEN_SPACE_TOP'])
  self.assertLess(HEIGHTS['OPEN_SPACE_TOP'],HEIGHTS['PATH_TOP'])
  self.assertTrue(.003<=HEIGHTS['DETAIL_EPSILON']<=.010)
 def test_inward_and_three_yaw(self):
  import math
  for poly in [box(0,0,20,20),box(0,0,20,20).reverse()]:
   point,yaw=boundary_frame(poly,5,1.2)
   self.assertAlmostEqual(poly.boundary.distance(point),1.2)
   self.assertTrue(poly.contains(point))
   a=poly.exterior.interpolate(4.9); b=poly.exterior.interpolate(5.1)
   # Three rotation of local +X = (cos(yaw),0,-sin(yaw)).
   self.assertAlmostEqual(math.atan2(b.y-a.y,b.x-a.x),yaw)
 def context(self):
  c=Context.__new__(Context); c.path=Point(100,100).buffer(1); c.paths=[]; c.owner_path_masks={}; c.road=c.path;c.building=c.path;c.environment={}
  return c
 def item(self):
  return dict(category='TREE_CLUSTER',position=[10,-10],source_id='test',placement_rule='PARK_GRID',yaw_rad=0)
 def test_obstacles(self):
  for field,reason in [('path','walkway'),('road','road'),('building','building')]:
   c=self.context();setattr(c,field,box(9,9,11,11))
   self.assertEqual(c.rejection(self.item(),box(0,0,30,30),[]),reason)
 def test_mapped_authority(self):
  c=self.context();c.environment={'mapped':('TREE_GENERIC',Point(14,10))}
  self.assertEqual(c.rejection(self.item(),box(0,0,30,30),[]),'existing_object')
 def test_spacing(self):
  c=self.context(); other=self.item();other['position']=[16,-10]
  self.assertEqual(c.rejection(self.item(),box(0,0,30,30),[other]),'spacing')
 def test_empty_eligible_area(self):
  self.assertEqual(self.context().rejection(self.item(),box(0,0,1,1),[]),'outside_owner')
if __name__=='__main__': unittest.main()
