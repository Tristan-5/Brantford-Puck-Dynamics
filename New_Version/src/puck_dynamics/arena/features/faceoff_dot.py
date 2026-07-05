"""
Eight face-off dots : one at centre ice, two in the neutral zone,
and five associated with the circles.

Specifications (Rule 1.9)
------------------------
• Diameter ........ 1 ft (0.3048 m)  – except centre-ice: 2 ft (0.6096 m)  
• Colour .......... red (handled by renderer)
• Height .......... 2 mm for visibility

Dot layout (rink coordinates)
----------------
Centre-ice ............................ (0, 0)  

Neutral-zone dots (in lieu of circles)  
  – X = ±20 ft from centreline, Y = 0  

End-zone dots – same centres as circles  
  (±(x_goal − 20 ft), ±11 ft)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence

from puck_dynamics.geometry import Cylinder, Point3D  # type: ignore[attr-defined]

from ..base import ArenaFeature
from ..dimensions import NHLStandardDimensions, ft_to_m
from .. import register_feature

__all__ = ["FaceoffDots"]

D_STD = ft_to_m(1)           # 1-ft diameter for regular dots
D_CTR = ft_to_m(2)           # 2-ft diameter at centre ice
PAINT_Z = 0.002

R_STD = D_STD / 2
R_CTR = D_CTR / 2

NEUTRAL_X = ft_to_m(20)
END_DOT_Y = ft_to_m(22) / 2      # 11 ft

@dataclass(frozen=True, slots=True)
class FaceoffDots(ArenaFeature):
    """Centre-ice plus seven additional face-off dots."""

    dims: NHLStandardDimensions = NHLStandardDimensions()
    name: str = "faceoff_dots"

    _cache: Sequence[object] | None = field(default=None, init=False, repr=False)

    def geometry(self) -> Sequence[object]:
        if self._cache is not None:
            return self._cache

        half_len = self.dims.length / 2
        x_goal   = half_len - self.dims.goal_line_distance

        centres_radii = [
            # centre ice
            (0.0, 0.0, R_CTR),
            # neutral-zone dots
            (+NEUTRAL_X, 0.0, R_STD),
            (-NEUTRAL_X, 0.0, R_STD),
        ]

        # four end-zone dots (same x as circle centres, y = ±11 ft)
        for sign_x in (+1, -1):
            x = sign_x * (x_goal - ft_to_m(20))
            centres_radii.append((x, +END_DOT_Y, R_STD))
            centres_radii.append((x, -END_DOT_Y, R_STD))

        geom: List[object] = [
            Cylinder(
                base_center=Point3D(cx, cy, 0.0),
                axis=Point3D(0, 0, 1),
                radius=r,
                height=PAINT_Z,
            )
            for cx, cy, r in centres_radii
        ]

        object.__setattr__(self, "_cache", tuple(geom))
        return self._cache

    def collision_surfaces(self) -> Sequence[object]:
        return []


register_feature("faceoff_dots", FaceoffDots)
