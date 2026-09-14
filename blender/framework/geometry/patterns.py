"""Reusable, deterministic facade pattern descriptions.

The records are Blender-independent so package/build tests can validate the
architectural logic without launching Blender.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WindowGrid:
    columns: int
    rows: int
    u0: float
    u1: float
    v0: float
    v1: float
    cell_fill_u: float = 0.58
    cell_fill_v: float = 0.56

    def regions(self) -> list[tuple[float, float, float, float]]:
        if self.columns < 1 or self.rows < 1:
            raise ValueError("window grid requires positive rows and columns")
        if not (0 <= self.u0 < self.u1 <= 1 and 0 <= self.v0 < self.v1 <= 1):
            raise ValueError("window grid bounds must be normalized")
        if not (0 < self.cell_fill_u <= 1 and 0 < self.cell_fill_v <= 1):
            raise ValueError("window grid cell fill must be in (0, 1]")
        du = (self.u1 - self.u0) / self.columns
        dv = (self.v1 - self.v0) / self.rows
        cells = []
        for row in range(self.rows):
            for column in range(self.columns):
                cx = self.u0 + (column + 0.5) * du
                cy = self.v0 + (row + 0.5) * dv
                half_u = du * self.cell_fill_u / 2
                half_v = dv * self.cell_fill_v / 2
                cells.append((cx - half_u, cx + half_u, cy - half_v, cy + half_v))
        return cells


@dataclass(frozen=True)
class OpenFacadeBand:
    """Vertical layout for a visually open floor band.

    The name intentionally describes observed geometry, not an asserted use.
    """

    base_z_m: float
    height_m: float
    slab_thickness_m: float = 0.35
    rail_height_m: float = 0.85

    def parts(self) -> dict[str, tuple[float, float]]:
        if self.height_m <= 0 or self.slab_thickness_m <= 0 or self.rail_height_m <= 0:
            raise ValueError("open facade band dimensions must be positive")
        if self.slab_thickness_m * 2 + self.rail_height_m >= self.height_m:
            raise ValueError("open facade band leaves no open zone")
        return {
            "bottom_slab": (self.base_z_m, self.slab_thickness_m),
            "open_zone": (
                self.base_z_m + self.slab_thickness_m,
                self.height_m - self.slab_thickness_m * 2,
            ),
            "guard_band": (
                self.base_z_m + self.slab_thickness_m,
                self.rail_height_m,
            ),
            "top_slab": (
                self.base_z_m + self.height_m - self.slab_thickness_m,
                self.slab_thickness_m,
            ),
        }
