"""
Goal‐keeper’s restricted area trapezoid (aka the “trapezoid rule”).

The shape is painted behind each goal between the goal line and the end
boards.  Model the two side lines and the rear connecting line as very thin
extruded boxes so 3-D renderers can show them in perspective.

Geometry is decorative only –xcluded from collision surfaces.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence

from puck_dynamics.geometry import Box3D  # type: ignore[attr-defined]

from ..base import ArenaFeature
from ..dimensions import NHLStandardDimensions, ft_to_m, in_to_m
from ..registry import register_feature

__all__ = ["Trapezoid"]

GOAL_LINE_WIDTH = ft_to_m(22)          # front edge length
BOARD_WIDTH     = ft_to_m(28)          # rear edge length
DEPTH           = ft_to_m(11)          # x-distance from goal line to boards
LINE_W          = in_to_m(2)           # 2-inch paint stripe
EXTRUDE         = 0.002                # 2 mm visual thickness


def _single_trapezoid(x_goal_line: float, half_wid: float) -> List[Box3D]:
    sign = 1 if x_goal_line > 0 else -1           # east = +1, west = −1

    # Y extents on goal line and board line
    y_half_front = GOAL_LINE_WIDTH / 2
    y_half_back  = BOARD_WIDTH / 2

    # X positions
    x_front = x_goal_line + sign * 0.0
    x_back  = x_goal_line + sign * DEPTH

    z0, z1 = 0.0, EXTRUDE
    geom: List[Box3D] = []

    # South-side slanted line
    y_min_south = min(-y_half_front - LINE_W / 2, -y_half_back + LINE_W / 2)
    y_max_south = max(-y_half_front - LINE_W / 2, -y_half_back + LINE_W / 2)
    geom.append(
        Box3D.from_bounds(
            x_min=min(x_front, x_back),
            x_max=max(x_front, x_back),
            y_min=y_min_south,
            y_max=y_max_south,
            z_min=z0,
            z_max=z1,
        )
    )
    # North-side slanted line
    y_min_north = min(+y_half_back - LINE_W / 2, +y_half_front + LINE_W / 2)
    y_max_north = max(+y_half_back - LINE_W / 2, +y_half_front + LINE_W / 2)
    geom.append(
        Box3D.from_bounds(
            x_min=min(x_front, x_back),
            x_max=max(x_front, x_back),
            y_min=y_min_north,
            y_max=y_max_north,
            z_min=z0,
            z_max=z1,
        )
    )
    # Rear line parallel to goal line (along Y)
    x_rear_min = min(x_back - LINE_W / 2 * sign, x_back + LINE_W / 2 * sign)
    x_rear_max = max(x_back - LINE_W / 2 * sign, x_back + LINE_W / 2 * sign)
    geom.append(
        Box3D.from_bounds(
            x_min=x_rear_min,
            x_max=x_rear_max,
            y_min=-y_half_back,
            y_max=+y_half_back,
            z_min=z0,
            z_max=z1,
        )
    )

    return geom


@dataclass(frozen=True, slots=True)
class Trapezoid(ArenaFeature):
    """Painted goalkeeper-restricted trapezoids (both ends)."""

    dims: NHLStandardDimensions = NHLStandardDimensions()
    name: str = "trapezoid"

    _cache: Sequence[object] | None = field(default=None, init=False, repr=False)

    def geometry(self) -> Sequence[object]:
        if self._cache is not None:
            return self._cache

        half_len = self.dims.length / 2
        x_goal_east =  half_len - self.dims.goal_line_distance
        x_goal_west = -x_goal_east
        half_wid = self.dims.width / 2

        geom: List[object] = []
        geom.extend(_single_trapezoid(x_goal_east, half_wid))
        geom.extend(_single_trapezoid(x_goal_west, half_wid))

        object.__setattr__(self, "_cache", tuple(geom))
        return self._cache

    def collision_surfaces(self) -> Sequence[object]:
        return []            # paint only


register_feature("trapezoid", Trapezoid)
