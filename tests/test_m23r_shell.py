"""Depth-competition fixtures independent of the live building dataset."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/m23'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/m23r'))
from build import Package
from facade_shell import compile_shell
from audit import overlap_report


class FacadeShellTest(unittest.TestCase):
    def report(self,p):
        return overlap_report(dict(id=p.id,meshes=p.meshes,instances=p.instances))['counts']

    def test_duplicate_boxes_detected_then_removed(self):
        p=Package('fixture','landmark')
        for _ in range(2):p.block(0,0,0,10,2,20,'GLASS_BLUE')
        self.assertGreater(self.report(p).get('EXACT_DUPLICATE',0),0)
        compile_shell(p)
        self.assertEqual(self.report(p).get('EXACT_DUPLICATE',0),0)
        self.assertEqual(self.report(p).get('COPLANAR',0),0)

    def test_cross_material_partial_overlap(self):
        p=Package('fixture','landmark')
        p.block(0,0,0,10,2,20,'GLASS_BLUE')
        p.block(3,0,5,10,2,5,'STONE_LIGHT')
        self.assertGreater(self.report(p).get('COPLANAR',0),0)
        compile_shell(p)
        self.assertEqual(self.report(p).get('COPLANAR',0),0)

    def test_separated_facades_are_preserved(self):
        p=Package('fixture','landmark')
        p.block(0,0,0,10,2,20,'GLASS_BLUE')
        p.block(0,4,0,10,2,20,'GLASS_BLUE')
        self.assertEqual(self.report(p),{})
        compile_shell(p)
        self.assertEqual(self.report(p),{})

    def test_near_coplanar_front_is_clipped_without_displacement(self):
        p=Package('fixture','landmark')
        p.block(0,0,0,10,2,20,'GLASS_BLUE')
        p.block(0,.01,0,5,2,10,'STONE_LIGHT')
        self.assertGreater(self.report(p).get('NEAR_COPLANAR',0),0)
        compile_shell(p)
        self.assertEqual(self.report(p).get('NEAR_COPLANAR',0),0)


if __name__=='__main__':unittest.main()
