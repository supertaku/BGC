"""Deterministic checks for the BGC geographic coordinate contract."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from shapely.geometry import Polygon


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "geography"))
from geo_utils import (
    ORIGIN_PROJECTED,
    ORIGIN_WGS84,
    euclidean_distance_m,
    geodesic_distance_m,
    local_to_wgs84,
    local_xy,
    polygon_area,
    signed_polygon_area,
    wgs84_to_utm51n,
)


def main() -> None:
    easting, northing = wgs84_to_utm51n(123.0, 0.0)
    assert math.isclose(easting, 500000.0, abs_tol=0.001)
    assert math.isclose(northing, 0.0, abs_tol=0.001)
    assert 280000 < ORIGIN_PROJECTED[0] < 300000
    assert 1_600_000 < ORIGIN_PROJECTED[1] < 1_620_000

    assert local_xy(*ORIGIN_WGS84) == (0.0, 0.0)
    round_trip = local_to_wgs84(*local_xy(*ORIGIN_WGS84))
    assert math.isclose(round_trip[0], ORIGIN_WGS84[0], abs_tol=1e-10)
    assert math.isclose(round_trip[1], ORIGIN_WGS84[1], abs_tol=1e-10)

    east_wgs84 = (ORIGIN_WGS84[0] + 0.001, ORIGIN_WGS84[1])
    north_wgs84 = (ORIGIN_WGS84[0], ORIGIN_WGS84[1] + 0.001)
    east = local_xy(*east_wgs84)
    north = local_xy(*north_wgs84)
    assert 107.0 < east[0] < 108.5 and abs(east[1]) < 1.2
    assert 110.0 < north[1] < 111.5 and abs(north[0]) < 1.2

    for target in (east_wgs84, north_wgs84, (121.0480, 14.5520)):
        projected_distance = euclidean_distance_m((0.0, 0.0), local_xy(*target))
        geodesic_distance = geodesic_distance_m(ORIGIN_WGS84, target)
        assert abs(projected_distance - geodesic_distance) < 0.25

    pilot = json.loads((ROOT / "data" / "geographic" / "pilot-boundary.geojson").read_text(encoding="utf-8"))
    ring = pilot["features"][0]["geometry"]["coordinates"][0][:-1]
    local_ring = [local_xy(longitude, latitude) for longitude, latitude in ring]
    area = polygon_area(local_ring)
    assert 190000 < area < 220000
    assert signed_polygon_area(local_ring) > 0
    assert signed_polygon_area(list(reversed(local_ring))) < 0
    assert Polygon(local_ring).is_valid
    width = max(x for x, _ in local_ring) - min(x for x, _ in local_ring)
    depth = max(y for _, y in local_ring) - min(y for _, y in local_ring)
    assert max(abs(value) for point in local_ring for value in point) < 500
    print(
        "BGC_COORDINATES: PASS "
        f"origin_e={ORIGIN_PROJECTED[0]:.3f} origin_n={ORIGIN_PROJECTED[1]:.3f} "
        f"pilot_width_m={width:.1f} pilot_depth_m={depth:.1f} area_ha={area / 10000:.2f}"
    )


if __name__ == "__main__":
    main()
