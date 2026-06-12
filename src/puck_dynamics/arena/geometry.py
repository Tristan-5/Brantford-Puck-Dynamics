"""Simplified rink geometry."""

from __future__ import annotations
from dataclasses import dataclass

RINK_LENGTH = 60.96   # m
RINK_WIDTH = 25.90    # m

GOAL_X = 57.0

SLOT_CENTER = (53.0, 12.95)

POINT_LEFT = (45.0, 6.0)
POINT_RIGHT = (45.0, 20.0)


@dataclass
class RinkGeometry:
    length_m: float = 60.96
    width_m: float = 25.91
    net_zone_depth_m: float = 4.0
    glass_height_m: float = 1.2
