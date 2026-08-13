"""
NHL blue lines – two 30 cm-wide stripes that divide the rink into three
zones.  They are painted on the ice and therefore have zero height for
physical collision purposes but exist as geometry so renderers can display
and analytics can query zone boundaries.

Rulebook facts
-------------
• Width: exactly 12 in (0.3048 m)  
• Location: the near edge of each line is 64 ft (19.5072 m) from the
  respective end boards (Rule 9.2).

Implementation notes
------------
i model each stripe as a very thin Box3D from z = 0 to
z = paint_thickness (default = 2 mm) so that a 3-D renderer can still
give the line some visible thickness without affecting puck physics.

"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence

from puck_dynamics.geometry import Box3D  # type: ignore[attr-defined]

from ..base import ArenaFeature
from ..dimensions import NHLStandardDimensions, ft_to_m
from ..registry import register_feature

__all__ = ["BlueLines"]


LINE_WIDTH_M = ft_to_m(1)  # 12 in → 0.3048 m
PAINT_THICKNESS = 0.002    # 2 mm – visually pleasing, physically negligible


@dataclass(frozen=True, slots=True)
class BlueLines(ArenaFeature):
    dims: NHLStandardDimensions = NHLStandardDimensions()
    paint_thickness: float = PAINT_THICKNESS
    name: str = "blue_lines"

    _geom_cache: Sequence[object] | None = field(default=None, init=False, repr=False, compare=False)


    def geometry(self) -> Sequence[object]:
        if self._geom_cache is not None:
            return self._geom_cache

        half_len = self.dims.length / 2.0
        half_wid = self.dims.width / 2.0

        near_edge_dist = self.dims.blue_line_distance
        far_edge_west = -half_len + near_edge_dist + LINE_WIDTH_M
        near_edge_west = -half_len + near_edge_dist

        near_edge_east = +half_len - near_edge_dist
        far_edge_east = near_edge_east - LINE_WIDTH_M

        z0, z1 = 0.0, self.paint_thickness

        geom: List[object] = [
            # West-side blue line
            Box3D.from_bounds(
                x_min=near_edge_west,
                x_max=far_edge_west,
                y_min=-half_wid,
                y_max=+half_wid,
                z_min=z0,
                z_max=z1,
            ),
            # East-side blue line
            Box3D.from_bounds(
                x_min=far_edge_east,
                x_max=near_edge_east,
                y_min=-half_wid,
                y_max=+half_wid,
                z_min=z0,
                z_max=z1,
            ),
        ]

        object.__setattr__(self, "_geom_cache", tuple(geom))
        return self._geom_cache

    def collision_surfaces(self) -> Sequence[object]:
        """
        Blue lines dont participate in puck collision – return empty.
        """
        return []


register_feature("blue_lines", BlueLines)
