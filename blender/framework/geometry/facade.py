"""Facade-local coordinates shared by evidence observations and Blender builders."""

from __future__ import annotations

from dataclasses import dataclass
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class FacadeFrame:
    """A horizontal facade frame using normalized u, vertical v, and depth d.

    ``u`` and ``v`` are normally in [0, 1]. ``d`` is metres, positive in the
    frame's outward-normal direction. Values outside [0, 1] are accepted for
    intentional projections, while regions are validated separately.
    """

    origin: tuple[float, float]
    length_m: float
    height_m: float
    angle_deg: float
    outward_sign: float = 1.0

    def __post_init__(self) -> None:
        if self.length_m <= 0 or self.height_m <= 0:
            raise ValueError("facade length and height must be positive")
        if self.outward_sign not in (-1.0, 1.0):
            raise ValueError("facade outward_sign must be -1 or 1")

    @property
    def along(self) -> tuple[float, float]:
        angle = math.radians(self.angle_deg)
        return math.cos(angle), math.sin(angle)

    @property
    def outward(self) -> tuple[float, float]:
        x, y = self.along
        return -y * self.outward_sign, x * self.outward_sign

    def point(self, u: float, d_m: float = 0.0) -> tuple[float, float]:
        along_x, along_y = self.along
        out_x, out_y = self.outward
        distance = u * self.length_m
        return (
            self.origin[0] + along_x * distance + out_x * d_m,
            self.origin[1] + along_y * distance + out_y * d_m,
        )

    def region(self, u0: float, u1: float, v0: float, v1: float, d_m: float = 0.0) -> dict:
        if not (0 <= u0 < u1 <= 1 and 0 <= v0 < v1 <= 1):
            raise ValueError("facade region requires 0 <= u0 < u1 <= 1 and 0 <= v0 < v1 <= 1")
        return {
            "center_xy": self.point((u0 + u1) / 2, d_m),
            "center_z": (v0 + v1) * self.height_m / 2,
            "width_m": (u1 - u0) * self.length_m,
            "height_m": (v1 - v0) * self.height_m,
            "depth_m": d_m,
        }


def polygon_signed_area(ring: list[list[float]]) -> float:
    """Return signed XY area; positive means counter-clockwise winding."""
    points = ring[:-1] if len(ring) > 1 and ring[0] == ring[-1] else ring
    if len(points) < 3:
        raise ValueError("polygon ring requires at least three distinct points")
    return 0.5 * sum(
        points[index][0] * points[(index + 1) % len(points)][1]
        - points[(index + 1) % len(points)][0] * points[index][1]
        for index in range(len(points))
    )


@dataclass(frozen=True)
class PolygonEdgeFrame:
    """Facade-local frame derived from one arbitrary polygon exterior edge."""

    start: tuple[float, float]
    end: tuple[float, float]
    height_m: float
    winding: float

    @classmethod
    def from_ring(cls, ring: list[list[float]], edge_index: int, height_m: float):
        points = ring[:-1] if len(ring) > 1 and ring[0] == ring[-1] else ring
        if not 0 <= edge_index < len(points):
            raise IndexError(f"edge index {edge_index} outside polygon with {len(points)} edges")
        start = tuple(float(value) for value in points[edge_index][:2])
        end = tuple(float(value) for value in points[(edge_index + 1) % len(points)][:2])
        if math.dist(start, end) <= 1e-6:
            raise ValueError(f"polygon edge {edge_index} is degenerate")
        return cls(start, end, height_m, polygon_signed_area(ring))

    @property
    def length_m(self) -> float:
        return math.dist(self.start, self.end)

    @property
    def angle_deg(self) -> float:
        return math.degrees(math.atan2(self.end[1] - self.start[1], self.end[0] - self.start[0]))

    @property
    def outward(self) -> tuple[float, float]:
        dx = (self.end[0] - self.start[0]) / self.length_m
        dy = (self.end[1] - self.start[1]) / self.length_m
        return (dy, -dx) if self.winding > 0 else (-dy, dx)

    def region(self, u0: float, u1: float, v0: float, v1: float, depth_m: float = 0.0) -> dict:
        if not (0 <= u0 < u1 <= 1 and 0 <= v0 < v1 <= 1):
            raise ValueError("polygon edge region requires normalized u/v bounds")
        along_x = (self.end[0] - self.start[0]) / self.length_m
        along_y = (self.end[1] - self.start[1]) / self.length_m
        distance = ((u0 + u1) / 2) * self.length_m
        return {
            "center_xy": (
                self.start[0] + along_x * distance + self.outward[0] * depth_m,
                self.start[1] + along_y * distance + self.outward[1] * depth_m,
            ),
            "center_z": (v0 + v1) * self.height_m / 2,
            "width_m": (u1 - u0) * self.length_m,
            "height_m": (v1 - v0) * self.height_m,
            "angle_deg": self.angle_deg,
        }
