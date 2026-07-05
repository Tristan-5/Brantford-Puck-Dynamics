"""
Protective spectator-safety netting installed above the end-zone
shielding-glass.  It extends the full width of the end boards and wraps a few
metres around the corners, terminating where the side-glass height alone is
considered adequate.

Scope / purpose
--------------
• Gives the simulation a 3-D surface that “catches” lofted pucks so later
  analytics can build out-of-play heat-maps.  
• Rendering engines may replace the coarse planes with detailed mesh.

NHL installation
-------------------
Exact coverage varies per rink; League guidelines require that the netting
span at least the width of the boards (200 ft corners) and rise to the
building’s low steel (≈ 32 ft above the ice in many arenas).  Side-board
glass is already ~10 ft; i therefore add netting from 10 ft to 32 ft.

Model decisions
---------------
1. Two trapezoidal quads (front faces) – one behind each goal.  
2. Two side-wrap quads per end that project 6 m down the straight boards.  
3. Netting thickness set to 2 cm; physics treats it as a planar surface.  
4. Returned as collision surfaces so a puck that hits the net is “OUT”.

Constants can be tuned for individual arenas
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence

from puck_dynamics.geometry import Box3D  # type: ignore[attr-defined]

from ..base import ArenaFeature
from ..dimensions import NHLStandardDimensions, ft_to_m
from .. import register_feature

__all__ = ["Netting"]

GLASS_TOP = ft_to_m(10)      # side/end glass top ≈ 10 ft
NET_TOP   = ft_to_m(32)      # target net height ≈ 32 ft (~9.75 m)

WRAP_LEN  = 6.0             # how far the net wraps along the side boards
THICKNESS = 0.02            # 2 cm visual / collision thickness

def _single_end_net(x_goal_line: float,
                    rink_half_wid: float,
                    rink_half_len: float,
                    corner_r: float) -> List[Box3D]:
    sign = 1 if x_goal_line > 0 else -1

    # Net front plane flush with back of end-glass (same X as boards)
    x_inner_plane = sign * (rink_half_len + THICKNESS / 2)

    # Portion straight behind goal (between corners)
    y_min_straight = -(rink_half_wid - corner_r)
    y_max_straight = +(rink_half_wid - corner_r)

    z0, z1 = GLASS_TOP, NET_TOP

    geom: List[Box3D] = []

    # Main straight panel
    geom.append(Box3D.from_bounds(
        x_min=x_inner_plane - THICKNESS/2,
        x_max=x_inner_plane + THICKNESS/2,
        y_min=y_min_straight,
        y_max=y_max_straight,
        z_min=z0,
        z_max=z1,
    ))

    # Corner wrap panels (approximate with boxes tangent to corner)
    # We'll extend a constant WRAP_LEN down the side boards.
    y_wrap_outer = y_max_straight + WRAP_LEN
    # Re-use same for south side
    geom.append(Box3D.from_bounds(
        x_min=x_inner_plane - THICKNESS/2,
        x_max=x_inner_plane + THICKNESS/2,
        y_min=y_max_straight,
        y_max=y_wrap_outer,
        z_min=z0,
        z_max=z1,
    ))
    geom.append(Box3D.from_bounds(
        x_min=x_inner_plane - THICKNESS/2,
        x_max=x_inner_plane + THICKNESS/2,
        y_min=-y_wrap_outer,
        y_max=-y_max_straight,
        z_min=z0,
        z_max=z1,
    ))

    return geom

@dataclass(frozen=True, slots=True)
class Netting(ArenaFeature):
    """
    Protective spectator netting behind both goal-lines.
    """

    dims: NHLStandardDimensions = NHLStandardDimensions()
    name: str = "netting"

    _cache: Sequence[object] | None = field(default=None, init=False, repr=False)

    def geometry(self) -> Sequence[object]:
        if self._cache is not None:
            return self._cache

        half_len = self.dims.length / 2
        half_wid = self.dims.width / 2
        corner_r = self.dims.corner_radius

        x_goal_line_e =  half_len - self.dims.goal_line_distance
        x_goal_line_w = -x_goal_line_e

        geom: List[object] = []
        geom.extend(_single_end_net(x_goal_line_e, half_wid, half_len, corner_r))
        geom.extend(_single_end_net(x_goal_line_w, half_wid, half_len, corner_r))

        object.__setattr__(self, "_cache", tuple(geom))
        return self._cache

    def collision_surfaces(self) -> Sequence[object]:
        # Netting is critical for “puck out-of-play” detection.
        return self.geometry()

register_feature("netting", Netting)

