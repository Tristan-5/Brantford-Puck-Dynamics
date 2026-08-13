"""
Goal lines –two thin red lines used for goal-detection technology.

Rulebook
-------
• Width .......... 2 in  (0.0508 m)  
• Location ....... 11 ft (3.3528 m) from each end-boards’ inner edge  
• Span ........... entire rink width between straight boards

Physics wise they are paint; height is negligible
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from puck_dynamics.geometry import Box3D  # type: ignore[attr-defined]

from ..base import ArenaFeature
from ..dimensions import NHLStandardDimensions, ft_to_m
from ..registry import register_feature

__all__ = ["GoalLines"]

LINE_WIDTH_M = ft_to_m(2 / 12)     # 2 inches
PAINT_THICKNESS = 0.002            # 2 mm


@dataclass(frozen=True, slots=True)
class GoalLines(ArenaFeature):

    dims: NHLStandardDimensions = NHLStandardDimensions()
    paint_thickness: float = PAINT_THICKNESS
    name: str = "goal_lines"

    _cache: Sequence[object] | None = field(default=None, init=False, repr=False, compare=False)


    def geometry(self) -> Sequence[object]:
        if self._cache is None:
            half_wid = self.dims.width / 2.0
            z0, z1 = 0.0, self.paint_thickness

            x_pos = +self.dims.length / 2.0 - self.dims.goal_line_distance
            x_neg = -x_pos

            west = Box3D.from_bounds(
                x_min=x_neg - LINE_WIDTH_M / 2.0,
                x_max=x_neg + LINE_WIDTH_M / 2.0,
                y_min=-half_wid,
                y_max=+half_wid,
                z_min=z0,
                z_max=z1,
            )
            east = Box3D.from_bounds(
                x_min=x_pos - LINE_WIDTH_M / 2.0,
                x_max=x_pos + LINE_WIDTH_M / 2.0,
                y_min=-half_wid,
                y_max=+half_wid,
                z_min=z0,
                z_max=z1,
            )
            object.__setattr__(self, "_cache", (west, east))
        return self._cache

    def collision_surfaces(self) -> Sequence[object]:
        return []


register_feature("goal_lines", GoalLines)
