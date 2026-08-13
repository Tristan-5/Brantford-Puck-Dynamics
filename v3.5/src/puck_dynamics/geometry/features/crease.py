"""
Goal-keeper’s crease – the blue semi-circular paint area in front of each
goal frame.

Quick spec  (NHL Rulebook §1.7)
--------------------------
• Width ................................ 8 ft  (2.438 m)  
  – ie. 1 ft beyond each goal-post (6 ft opening)  
• Depth (centre line → apex) ........... 4 ft  (1.219 m)  
• Radius of semi-circle ................ 6 ft  (1.829 m) measured from the
  centre of the goal line to the outside edge of the line.  
• Line / paint thickness ............... 2 in  (0.0508 m)

Geometry generated
-----------------
1. A filled paint volume  (very thin Box3d + polygon fan) used only for
   rendering analytics – excluded from collision.  
2. Two identical creases: East (+X) and West (–X).

Because the crease is flat paint, its physical height is negligible; we
exaggerate it to 2 mm so 3-D renderers can show a surface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence
import math

from puck_dynamics.geometry import (               # type: ignore[attr-defined]
    Box3D,
    Point3D,
    Arc,
    Circle,
    Polyline2D,
)

from ..base import ArenaFeature
from ..dimensions import NHLStandardDimensions, ft_to_m, in_to_m
from ..registry import register_feature

__all__ = ["Crease"]


WIDTH   = ft_to_m(8)                  # full chord width
DEPTH   = ft_to_m(4)                  # rectangle depth before the arc
RADIUS  = ft_to_m(6)                  # outer radius of semi-circle
PAINT_T = in_to_m(2)                  # 2-inch stripe
EXTRUDE = 0.002                       # 2 mm visual thickness


def _single_crease(x_goal_line: float) -> List[object]:
    geom: List[object] = []
    sign = 1 if x_goal_line > 0 else -1     # east = +1, west = −1

    # The rectangle portion (goal line to 4 ft out)
    x_min = x_goal_line + sign * 0.0
    x_max = x_goal_line + sign * DEPTH
    y_min = -WIDTH / 2
    y_max = +WIDTH / 2

    # Painted rectangle
    geom.append(
        Box3D.from_bounds(
            x_min=min(x_min, x_max),
            x_max=max(x_min, x_max),
            y_min=y_min,
            y_max=y_max,
            z_min=0.0,
            z_max=EXTRUDE,
        )
    )

    # Semi-circular arc outline for renderers
    center_arc = (x_goal_line + sign * DEPTH, 0.0)
    start_ang, end_ang = (270, 90) if sign > 0 else (90, 270)  # CCW
    circle = Circle(center=Point3D(center_arc[0], center_arc[1], 0.0), normal=Point3D(0.0, 0.0, 1.0), radius=RADIUS)
    arc = Arc(
        circle=circle,
        start_angle=math.radians(start_ang),
        end_angle=math.radians(end_ang),
        clockwise=False,
    )
    geom.append(arc)

    # Polyline connecting rectangle to arc for nice outline
    outline_pts = [
        Point3D(x_min, y_min, 0),
        Point3D(x_max, y_min, 0),
    ] + arc.discretize(32) + [
        Point3D(x_max, y_max, 0),
        Point3D(x_min, y_max, 0),
        Point3D(x_min, y_min, 0),
    ]
    geom.append(Polyline2D(outline_pts))

    return geom


@dataclass(frozen=True, slots=True)
class Crease(ArenaFeature):
    """
    Both semi-circular goal-keeper creases.

    Purely decorative (no collision surfaces).
    """

    dims: NHLStandardDimensions = NHLStandardDimensions()
    name: str = "crease"

    _cache: Sequence[object] | None = field(default=None, init=False, repr=False)


    def geometry(self) -> Sequence[object]:
        if self._cache is not None:
            return self._cache

        half_len = self.dims.length / 2.0
        x_goal_line_e =  half_len - self.dims.goal_line_distance
        x_goal_line_w = -x_goal_line_e

        geom: List[object] = []
        geom.extend(_single_crease(x_goal_line_e))
        geom.extend(_single_crease(x_goal_line_w))

        object.__setattr__(self, "_cache", tuple(geom))
        return self._cache

    def collision_surfaces(self) -> Sequence[object]:
        return []          # paint only – ignored by physics


register_feature("crease", Crease)

