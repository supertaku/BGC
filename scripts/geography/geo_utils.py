"""Authoritative CRS helpers for the BGC local engineering frame.

All public functions accept longitude/latitude ordering. ``always_xy=True`` is
intentional: EPSG:4326's formal axis order differs from GeoJSON's x/y order.
"""

from __future__ import annotations

from collections.abc import Iterable
import math

try:
    from pyproj import CRS, Geod, Transformer
except ImportError as exc:  # pragma: no cover - exercised by setup failures
    raise RuntimeError(
        "Geospatial dependencies are missing. Install requirements-geospatial.txt."
    ) from exc


SOURCE_CRS = CRS.from_epsg(4326)
PROJECTED_CRS = CRS.from_epsg(32651)
ORIGIN_WGS84 = (121.050972, 14.550806)
_TRANSFORMER = Transformer.from_crs(SOURCE_CRS, PROJECTED_CRS, always_xy=True)
_INVERSE_TRANSFORMER = Transformer.from_crs(PROJECTED_CRS, SOURCE_CRS, always_xy=True)
ORIGIN_PROJECTED = _TRANSFORMER.transform(*ORIGIN_WGS84)
WGS84_GEOD = Geod(ellps="WGS84")


def wgs84_to_utm51n(longitude: float, latitude: float) -> tuple[float, float]:
    """Project a GeoJSON-order WGS84 point to EPSG:32651 metres."""
    if not (120.0 <= longitude <= 126.0 and 0.0 <= latitude < 84.0):
        raise ValueError("Coordinate is outside the project use area for EPSG:32651")
    easting, northing = _TRANSFORMER.transform(longitude, latitude, errcheck=True)
    return float(easting), float(northing)


def utm51n_to_wgs84(easting: float, northing: float) -> tuple[float, float]:
    """Invert EPSG:32651 to GeoJSON-order WGS84 longitude/latitude."""
    longitude, latitude = _INVERSE_TRANSFORMER.transform(easting, northing, errcheck=True)
    return float(longitude), float(latitude)


def local_xy(
    longitude: float,
    latitude: float,
    origin: tuple[float, float] = ORIGIN_WGS84,
) -> tuple[float, float]:
    """Return local east/north metres relative to a WGS84 origin."""
    easting, northing = wgs84_to_utm51n(longitude, latitude)
    origin_easting, origin_northing = (
        ORIGIN_PROJECTED if origin == ORIGIN_WGS84 else wgs84_to_utm51n(*origin)
    )
    return easting - origin_easting, northing - origin_northing


def local_to_wgs84(x: float, y: float) -> tuple[float, float]:
    """Invert a local east/north point to WGS84 longitude/latitude."""
    return utm51n_to_wgs84(ORIGIN_PROJECTED[0] + x, ORIGIN_PROJECTED[1] + y)


def geodesic_distance_m(first: tuple[float, float], second: tuple[float, float]) -> float:
    """Return ellipsoidal WGS84 distance for two longitude/latitude points."""
    _, _, distance = WGS84_GEOD.inv(first[0], first[1], second[0], second[1])
    return float(distance)


def point_in_polygon(point: tuple[float, float], ring: Iterable[Iterable[float]]) -> bool:
    """Boundary-inclusive ray casting retained for small dependency-light callers."""
    x, y = point
    vertices = [(float(px), float(py)) for px, py in ring]
    inside = False
    previous = vertices[-1]
    for current in vertices:
        x1, y1 = previous
        x2, y2 = current
        cross = (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)
        if abs(cross) < 1e-12 and min(x1, x2) <= x <= max(x1, x2) and min(y1, y2) <= y <= max(y1, y2):
            return True
        if (y1 > y) != (y2 > y):
            crossing_x = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x < crossing_x:
                inside = not inside
        previous = current
    return inside


def signed_polygon_area(points: list[tuple[float, float]]) -> float:
    """Signed planar polygon area; positive rings are counter-clockwise."""
    if len(points) < 3:
        return 0.0
    return sum(
        x1 * y2 - x2 * y1
        for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1])
    ) / 2.0


def polygon_area(points: list[tuple[float, float]]) -> float:
    return abs(signed_polygon_area(points))


def euclidean_distance_m(first: tuple[float, float], second: tuple[float, float]) -> float:
    return math.hypot(second[0] - first[0], second[1] - first[1])
