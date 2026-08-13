"""
NHL goal frame– posts, cross-bar and (optionally) the rectangular
goal-crease volume.

For simulation only the metal frame matters; the flexible net is ignored
here and, if ever needed, can be added in the physics package as a
thin spring-mesh.

Rulebook essentials
----------------------
• Opening width ........ 6 ft   (1.829 m inside face to inside face)  
• Opening height ....... 4 ft   (1.219 m ice to underside of cross-bar)  
• Depth at ice level ... 44 in  (1.1176 m from goal line to rear frame)  
• Post ⌀ (OD) .......... 2⅜ in  (0.0603 m) — we model as solid cylinders  
• Cross-bar ⌀ .......... same as posts

Geometry produced
----------------
┌ East goal  (positive X) ┐
│ • two vertical cylinders (posts)    
│ • one horizontal cylinder (cross-bar)        
└ plus identical West goal (mirrored) ┘

All components share a single colour (renderer decides).

Collision model
--------------
The cylinders themselves form the collision surfaces; no need for an
enclosing box.  Puck radius (approx. 0.038 m) is comparable to post radius so
this granularity is adequate.

"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence, Tuple

from puck_dynamics.geometry import Cylinder, Point3D  # type: ignore[attr-defined]

from ..base import ArenaFeature
from ..dimensions import NHLStandardDimensions, ft_to_m, in_to_m
from ..registry import register_feature

__all__ = ["Goals"]

GOAL_WIDTH = ft_to_m(6)                    # inside face width  1.829 m
GOAL_HEIGHT = ft_to_m(4)                   # 1.219 m
GOAL_DEPTH = in_to_m(44)                   # 1.1176 m
POST_DIAMETER = in_to_m(2 + 3 / 8)         # 2⅜ in  → 0.06033 m
POST_RADIUS = POST_DIAMETER / 2.0
CROSSBAR_RADIUS = POST_RADIUS              # same tubing
ICE_Z = 0.0



def _single_goal_geometry(
    x_goal_line: float,  # position of goal line (+ve east, −ve west)
    dims: NHLStandardDimensions,
) -> List[Cylinder]:
    # Posts centres sit one radius behind the goal line
    x_post_centre = x_goal_line - POST_RADIUS if x_goal_line > 0 else x_goal_line + POST_RADIUS
    half_opening = GOAL_WIDTH / 2.0
    y_north = +half_opening
    y_south = -half_opening

    z0 = ICE_Z
    z1 = GOAL_HEIGHT

    # Two vertical posts
    post_n = Cylinder(
        base_center=Point3D(x_post_centre, y_north, z0),
        axis=Point3D(0, 0, 1),
        radius=POST_RADIUS,
        height=z1 - z0,
    )
    post_s = Cylinder(
        base_center=Point3D(x_post_centre, y_south, z0),
        axis=Point3D(0, 0, 1),
        radius=POST_RADIUS,
        height=z1 - z0,
    )

    # Horizontal cross-bar (single cylinder along Y)
    # Centre line sits at z = GOAL_HEIGHT
    crossbar = Cylinder(
        base_center=Point3D(x_post_centre, y_south, z1),
        axis=Point3D(0, 1, 0),  # along +Y
        radius=CROSSBAR_RADIUS,
        height=GOAL_WIDTH,
    )

    return [post_n, post_s, crossbar]


@dataclass(frozen=True, slots=True)
class Goals(ArenaFeature):

    dims: NHLStandardDimensions = NHLStandardDimensions()
    name: str = "goals"

    _cache: Sequence[object] | None = field(default=None, init=False, repr=False)


    def geometry(self) -> Sequence[object]:
        if self._cache is not None:
            return self._cache

        half_len = self.dims.length / 2.0
        x_goal_line_east = +half_len - self.dims.goal_line_distance
        x_goal_line_west = -x_goal_line_east

        geom: List[object] = []
        geom.extend(_single_goal_geometry(x_goal_line_east, self.dims))
        geom.extend(_single_goal_geometry(x_goal_line_west, self.dims))

        object.__setattr__(self, "_cache", tuple(geom))
        return self._cache

    # Collision surfaces are identical to geometry
    def collision_surfaces(self) -> Sequence[object]:
        return self.geometry()

register_feature("goals", Goals)
