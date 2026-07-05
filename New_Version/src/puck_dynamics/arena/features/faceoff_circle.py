"""
All five face-off circles (one centre-ice, four in the end-zones)--left off the neutral zone ones.

Rulebook (NHL §1.9 – §1.10)
-----------------
• Radius .................... 15 ft  (4.572 m) measured to *outside* edge  
• Line / paint width ........ 2 in   (0.0508 m)  
• Height (for rendering) .... 2 mm   – negligible in physics

Geometry strategy
----------------
Each circle is modelled as a very thin hollow cylinder (“washer”):
outer-radius = 15 ft, inner-radius = 15 ft – line-width.

Locations (in rink coords)
------------------------
(1) Centre-ice .................. (0, 0)  
(2) NE zone  ( +20 ft behind goal-line,  +22 ft/2 left-right)  
(3) SE zone  ( +20 ft,                −22 ft/2)  
(4) NW zone  (−20 ft,                +22 ft/2)  
(5) SW zone  (−20 ft,                −22 ft/2)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence, List

from puck_dynamics.geometry import HollowCylinder, Point3D  # type: ignore[attr-defined]

from ..base import ArenaFeature
from ..dimensions import NHLStandardDimensions, ft_to_m, in_to_m
from .. import register_feature

__all__ = ["FaceoffCircles"]

R_OUT      = ft_to_m(15)
LINE_W     = in_to_m(2)
R_IN       = R_OUT - LINE_W
PAINT_Z    = 0.002

SPOT_X = ft_to_m(20)     # distance from goal-line
SPOT_Y = ft_to_m(22) / 2 # half lateral spacing

@dataclass(frozen=True, slots=True)
class FaceoffCircles(ArenaFeature):

    dims: NHLStandardDimensions = NHLStandardDimensions()
    name: str = "faceoff_circles"

    _cache: Sequence[object] | None = field(default=None, init=False, repr=False)

    def geometry(self) -> Sequence[object]:
        if self._cache is not None:
            return self._cache

        half_len = self.dims.length / 2
        x_goal   = half_len - self.dims.goal_line_distance

        centres = [
            (0.0, 0.0),                        # centre-ice
            ( +x_goal - SPOT_X, +SPOT_Y),
            ( +x_goal - SPOT_X, -SPOT_Y),
            ( -x_goal + SPOT_X, +SPOT_Y),
            ( -x_goal + SPOT_X, -SPOT_Y),
        ]

        geom: List[object] = [
            HollowCylinder(
                base_center=Point3D(cx, cy, 0.0),
                axis=Point3D(0, 0, 1),
                outer_radius=R_OUT,
                inner_radius=R_IN,
                height=PAINT_Z,
            )
            for cx, cy in centres
        ]

        object.__setattr__(self, "_cache", tuple(geom))
        return self._cache

    def collision_surfaces(self) -> Sequence[object]:
        return []                       # paint only


register_feature("faceoff_circles", FaceoffCircles)
