"""
Rink boards (dasher) with rounded 28-ft corners.

The class produces *collision-accurate* geometry that later layers (physics,
simulation) can query.  It deliberately omits colour or texture decisions—those
live in the renderer

1. Straight runs are axis-aligned :class:`puck_dynamics.geometry.Box3D`
   prisms whose Y–Z faces form the physical wall.

2. Corner sections are modelled as full :class:`~puck_dynamics.geometry.Cylinder`
   shells because the geometry package (v1) has no “partial cylinder” surface.
   The extra 3/4 volume outside the rink is harmless for collision detection
   (puck and players never reach it) and simplifies maths.

3. All coordinates follow the rink frame defined in
   :pymod:`puck_dynamics.arena.coordinate_system`.

4. The class self-registers with the arena plug-in registry so
   `CivicCenter()` can discover it automatically.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence

from puck_dynamics.geometry import Box3D, Cylinder, Point3D  # type: ignore[attr-defined]

from ..base import ArenaFeature
from ..dimensions import NHLStandardDimensions
from .. import register_feature

__all__ = ["Boards"]


@dataclass(frozen=True, slots=True)
class Boards(ArenaFeature):

    dims: NHLStandardDimensions = NHLStandardDimensions()
    thickness: float = 0.1524  # 6 in
    name: str = "boards"

    _geom_cache: Sequence[object] | None = field(default=None, init=False, repr=False, compare=False)

    def geometry(self) -> Sequence[object]:
        # cached?
        if self._geom_cache is not None:
            return self._geom_cache

        half_len = self.dims.length / 2.0
        half_wid = self.dims.width / 2.0
        r = self.dims.corner_radius
        h0, h1 = 0.0, self.dims.board_height

        geom: List[object] = []

        # 1. North side (positive Y) – between corners
        north_y = half_wid
        north_x0 = -(half_len - r)
        north_x1 = +(half_len - r)
        geom.append(
            Box3D.from_bounds(
                x_min=north_x0,
                x_max=north_x1,
                y_min=north_y - self.thickness,
                y_max=north_y,
                z_min=h0,
                z_max=h1,
            )
        )

        # 2. South side (negative Y)
        south_y = -half_wid
        geom.append(
            Box3D.from_bounds(
                x_min=north_x0,
                x_max=north_x1,
                y_min=south_y,
                y_max=south_y + self.thickness,
                z_min=h0,
                z_max=h1,
            )
        )

        # 3. East end boards (+X)
        east_x = half_len
        east_y0 = -(half_wid - r)
        east_y1 = +(half_wid - r)
        geom.append(
            Box3D.from_bounds(
                x_min=east_x - self.thickness,
                x_max=east_x,
                y_min=east_y0,
                y_max=east_y1,
                z_min=h0,
                z_max=h1,
            )
        )

        # 4. West end boards (−X)
        west_x = -half_len
        geom.append(
            Box3D.from_bounds(
                x_min=west_x,
                x_max=west_x + self.thickness,
                y_min=east_y0,
                y_max=east_y1,
                z_min=h0,
                z_max=h1,
            )
        )

        centres = [
            (+half_len - r, +half_wid - r),
            (+half_len - r, -half_wid + r),
            (-half_len + r, -half_wid + r),
            (-half_len + r, +half_wid - r),
        ]
        for cx, cy in centres:
            geom.append(
                Cylinder(
                    base_center=Point3D(cx, cy, h0),
                    axis=Point3D(0, 0, 1),  # vertical
                    radius=r,
                    height=h1 - h0,
                )
            )

        object.__setattr__(self, "_geom_cache", tuple(geom))
        return self._geom_cache
    def collision_surfaces(self) -> Sequence[object]:
        return self.geometry()

register_feature("boards", Boards)

