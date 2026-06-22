"""Boundary checks for glass, boards, and netting."""

from __future__ import annotations
from dataclasses import dataclass
from .geometry import RinkGeometry


@dataclass
class BoundaryResult:
    hit_glass: bool = False
    hit_netting: bool = False
    out_of_play: bool = False


def check_boundaries(x: float, y: float, geom: RinkGeometry) -> BoundaryResult:
    """Determine whether a point is beyond the simple arena boundaries."""
    hit_glass = abs(y) > geom.width_m / 2
    hit_netting = x > geom.length_m - geom.net_zone_depth_m and abs(y) < 5.0
    out_of_play = hit_glass or hit_netting or x < 0 or x > geom.length_m
    return BoundaryResult(hit_glass=hit_glass, hit_netting=hit_netting, out_of_play=out_of_play)

"""Arena boundaries and spectator geometry."""

BOARD_HEIGHT = 1.22
GLASS_HEIGHT = 2.44

RINK_X_MIN = 35.0
RINK_X_MAX = 60.96

RINK_Y_MIN = 0.0
RINK_Y_MAX = 25.90

NETTING_X = 57.0
NETTING_Y_MIN = 4.0
NETTING_Y_MAX = 22.0
NETTING_HEIGHT = 12.0
