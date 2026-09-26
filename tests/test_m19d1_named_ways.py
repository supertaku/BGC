import json
import math
import unittest
from collections import defaultdict
from pathlib import Path

from shapely.geometry import LineString, box

from scripts.geography.build_interactive_runtime import named_ways


ROOT = Path(__file__).resolve().parents[1]


class NamedWaysTest(unittest.TestCase):
    def test_clips_lines_and_geometry_collection(self):
        feature = {"properties": {"id": "osm:way:1", "name": "Test Street", "class": "residential",
                                  "width_m": 8, "tags": {"alt_name": "Old Street"},
                                  "centerline_local": {"type": "GeometryCollection", "geometries": [
                                      {"type": "LineString", "coordinates": [[-5, 5], [15, 5]]},
                                      {"type": "MultiLineString", "coordinates": [[[2, 0], [2, 10]]]}
                                  ]}}}
        ways = named_ways({"bounds": [0, 0, 10, 10], "roads": [feature], "paths": []})
        self.assertGreaterEqual(len(ways), 2)
        self.assertEqual({way["id"] for way in ways}, {"osm:way:1"})
        self.assertEqual(ways[0]["aliases"], ["Old Street"])
        for way in ways:
            self.assertTrue(all(0 <= x <= 10 and -10 <= z <= 0 for x, z in way["points"]))

    def test_generated_sidecars(self):
        world = json.loads((ROOT / "web/public/world/bgc-world.json").read_text())
        counts = defaultdict(int)
        identities = defaultdict(set)
        for tile in world["tiles"]:
            sidecar = json.loads((ROOT / "web/public/world/tiles" / f'{tile["tile_id"]}.json').read_text())
            cell = box(*tile["bounds"])
            for way in sidecar.get("namedWays", []):
                counts[way["kind"]] += 1
                identities[way["id"]].add(way["name"])
                self.assertTrue(way["name"].strip())
                self.assertGreaterEqual(len(way["points"]), 2)
                self.assertTrue(all(math.isfinite(value) for point in way["points"] for value in point))
                line = LineString([(x, -z) for x, z in way["points"]])
                self.assertTrue(cell.buffer(0.02).intersects(line))
                self.assertTrue(all(cell.buffer(0.02).covers(line.interpolate(t, normalized=True)) for t in (0, .5, 1)))
        self.assertGreater(counts["ROAD"], 0)
        self.assertGreater(counts["PATH"], 0)
        self.assertTrue(all(len(names) == 1 for names in identities.values()))


if __name__ == "__main__":
    unittest.main()
