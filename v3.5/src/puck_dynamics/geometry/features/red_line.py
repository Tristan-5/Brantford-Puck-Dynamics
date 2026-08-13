"""
Centre-ice red line (a single 30 cm stripe that bisects the rink).

NHL rulebook
-----------
• Width .......... 12 in  (0.3048 m)  
• Location ....... exact geometric centre of the rink (x = 0)  
• Appearance ..... 2-inch alternating red/white squares; colour is the
  renderer’s job, geometry is a solid rectangular prism.

Like blue lines, the red line is extruded a tiny amount in the +Z direction
so that 3-D renderers can pick it up without affecting physics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from puck_dynamics.geometry import Box3D  # type: ignore[attr-defined]

from ..base import ArenaFeature
from ..dimensions import NHLStandardDimensions, ft_to_m
from ..registry import register_feature

__all__ = ["CenterRedLine"]

LINE_WIDTH_M = ft_to_m(1)          # 12 in
PAINT_THICKNESS = 0.002            # 2 mm


@dataclass(frozen=True, slots=True)
class CenterRedLine(ArenaFeature):

    dims: NHLStandardDimensions = NHLStandardDimensions()
    paint_thickness: float = PAINT_THICKNESS
    name: str = "center_red_line"

    _cache: Sequence[object] | None = field(default=None, init=False, repr=False, compare=False)

    def geometry(self) -> Sequence[object]:
        if self._cache is None:
            half_wid = self.dims.width / 2.0
            z0, z1 = 0.0, self.paint_thickness
            self_obj = Box3D.from_bounds(
                x_min=-LINE_WIDTH_M / 2.0,
                x_max=+LINE_WIDTH_M / 2.0,
                y_min=-half_wid,
                y_max=+half_wid,
                z_min=z0,
                z_max=z1,
            )
            object.__setattr__(self, "_cache", (self_obj,))
        return self._cache

    def collision_surfaces(self) -> Sequence[object]:
        return []


register_feature("center_red_line", CenterRedLine)
