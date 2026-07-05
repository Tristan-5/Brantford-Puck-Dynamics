"""
Penalty-box benches

Context
------
In NHL arenas the penalty boxes are located on the side opposite the player
benches (ie the north side in our coordinate frame).  They flank the
time-keeper’s/official scorer’s box at centre ice.

Typical modern-arena dimensions (from rink building guides):

• Inside length (along X) .............. 20 ft  (6.096 m) per box  
• Separation (time-keeper area) ........ 10 ft  (3.048 m) gap centred on x=0  
• Depth (behind boards) ................ 5 ft   (1.524 m)  
• Wall thickness (for render render) ... 2 in  (0.0508 m)  
• Seat-back / glass height (visual) .... 1.2 m above ice

Like the player benches, these volumes are off-ice and do not participate in
puck collision; they exist for line-change logic and rendering.

I model each box and the central official-area as simple Box3D`s so engine
code can query whether a puck / player / official is inside.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence, List, Dict

from puck_dynamics.geometry import Box3D  # type: ignore[attr-defined]

from ..base import ArenaFeature
from ..dimensions import NHLStandardDimensions, ft_to_m, in_to_m
from .. import register_feature

__all__ = ["PenaltyBoxes"]

BOX_LEN   = ft_to_m(20)            # 20-ft internal length
GAP_LEN   = ft_to_m(10)            # scorer's/time-keeper gap
DEPTH     = ft_to_m(5)             # behind the boards
WALL      = in_to_m(2)             # nominal wall thickness
HEIGHT    = 1.20                   # visible seat/glass height above ice


@dataclass(frozen=True, slots=True)
class PenaltyBoxes(ArenaFeature):

    dims: NHLStandardDimensions = NHLStandardDimensions()
    name: str = "penalty_boxes"

    _cache: Sequence[object] | None = field(default=None, init=False, repr=False)
    _meta:  Dict[str, Box3D] | None = field(default=None, init=False, repr=False)

    def geometry(self) -> Sequence[object]:
        if self._cache is not None:
            return self._cache

        half_len_rink = self.dims.length / 2
        half_wid_rink = self.dims.width / 2
        r_corner      = self.dims.corner_radius

        # North straight boards: x spans −(L−r) … +(L−r)
        straight_x_min = -(half_len_rink - r_corner)
        straight_x_max = +(half_len_rink - r_corner)

        y_inner = half_wid_rink + WALL       # just outside boards
        y_outer = y_inner + DEPTH

        # Position boxes symmetrically with 10-ft central gap
        gap_half = GAP_LEN / 2
        box_half = BOX_LEN / 2

        # West (away) box: centre at −(gap/2 + box_half)
        away_center_x = - (gap_half + box_half)
        away_box = Box3D.from_bounds(
            x_min=away_center_x - box_half,
            x_max=away_center_x + box_half,
            y_min=y_inner,
            y_max=y_outer,
            z_min=0.0,
            z_max=HEIGHT,
        )

        # East (home) box
        home_center_x = + (gap_half + box_half)
        home_box = Box3D.from_bounds(
            x_min=home_center_x - box_half,
            x_max=home_center_x + box_half,
            y_min=y_inner,
            y_max=y_outer,
            z_min=0.0,
            z_max=HEIGHT,
        )

        # Central official/time-keeper box (optional but handy for refs)
        center_box = Box3D.from_bounds(
            x_min=-gap_half,
            x_max=+gap_half,
            y_min=y_inner,
            y_max=y_outer,
            z_min=0.0,
            z_max=HEIGHT,
        )

        object.__setattr__(self, "_cache", (away_box, center_box, home_box))
        object.__setattr__(self, "_meta",
                           {"away_penalty_box": away_box,
                            "timekeeper_box": center_box,
                            "home_penalty_box": home_box})
        return self._cache

    def boxes(self) -> Dict[str, Box3D]:
        """
        Returns dictionary with descriptive keys pointing to Box3D volumes.
        """
        if self._meta is None:
            self.geometry()
        return self._meta           # type: ignore[return-value]

    def collision_surfaces(self) -> Sequence[object]:
        return []                   # off-ice → puck never hits

register_feature("penalty_boxes", PenaltyBoxes)

