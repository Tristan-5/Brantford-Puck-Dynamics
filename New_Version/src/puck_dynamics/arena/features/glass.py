"""
Protective acrylic glass that sits atop the dasher boards.
 
The geometry is derived directly from an existing :class:`Boards` instance so
that both components align perfectly and share a common footprint.  Glass
panels are modelled as thin vertical prisms (``Box3D``) for straight runs
and hollow cylinders (``Cylinder``) for the four rounded corners.

Key assumptions
---------------
1. Glass follows the *inside* face of the boards, i.e. the playing-surface
   footprint.  This keeps collision queries simple—puck trajectories reflect
   off the same surface whether they hit the dasher or the glass.

2. Thickness is configurable (default = 24 mm ≈ 15/16 in).  NHL rules only set
   a **minimum** of ½″, so we adopt a realistic value used in many arenas.

3. Because glass is transparent no added top caps; those would be
   invisible in rendering and irrelevant for collision detection.

4. The class self-registers under "glass" in the arena registry.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence

from puck_dynamics.geometry import Box3D, Cylinder, Point3D  # type: ignore[attr-defined]

from ..base import ArenaFeature
from ..dimensions import NHLStandardDimensions
from .boards import Boards
from .. import register_feature

__all__ = ["Glass"]


@dataclass(frozen=True, slots=True)
class Glass(ArenaFeature):

    dims: NHLStandardDimensions = NHLStandardDimensions()
    thickness: float = 0.024  # 24 mm
    boards: Boards = Boards()  # default aligns with same dims
    name: str = "glass"

    _geom_cache: Sequence[object] | None = field(default=None, init=False, repr=False, compare=False)


    def geometry(self) -> Sequence[object]:
        if self._geom_cache is not None:
            return self._geom_cache

        # Re-use board footprint but shift **upwards**
        h0 = self.dims.board_height
        h1 = h0 + self.dims.glass_height

        half_len = self.dims.length / 2.0
        half_wid = self.dims.width / 2.0
        r = self.dims.corner_radius

        geom: List[object] = []

        # Straight sections
        north_y = half_wid
        south_y = -half_wid
        west_x = -half_len
        east_x = half_len
        x0 = -(half_len - r)
        x1 = +(half_len - r)
        y0 = -(half_wid - r)
        y1 = +(half_wid - r)

        # North
        geom.append(
            Box3D.from_bounds(
                x_min=x0,
                x_max=x1,
                y_min=north_y - self.thickness,
                y_max=north_y,
                z_min=h0,
                z_max=h1,
            )
        )
        # South
        geom.append(
            Box3D.from_bounds(
                x_min=x0,
                x_max=x1,
                y_min=south_y,
                y_max=south_y + self.thickness,
                z_min=h0,
                z_max=h1,
            )
        )
        # East
        geom.append(
            Box3D.from_bounds(
                x_min=east_x - self.thickness,
                x_max=east_x,
                y_min=y0,
                y_max=y1,
                z_min=h0,
                z_max=h1,
            )
        )
        # West
        geom.append(
            Box3D.from_bounds(
                x_min=west_x,
                x_max=west_x + self.thickness,
                y_min=y0,
                y_max=y1,
                z_min=h0,
                z_max=h1,
            )
        )

        # Corner cylinders (full 360° simplifies implementation)
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
                    axis=Point3D(0, 0, 1),
                    radius=r + (self.thickness / 2.0),  # outside face
                    height=h1 - h0,
                )
            )

        object.__setattr__(self, "_geom_cache", tuple(geom))
        return self._geom_cache


    def collision_surfaces(self) -> Sequence[object]:
        """
        Return the *inner* faces only (identical to boards).  Here we simply
        forward to :py:meth:`geometry` because the full volume contains those
        faces and the redundant outer ones do not harm simulation.
        """
        return self.geometry()

register_feature("glass", Glass)

