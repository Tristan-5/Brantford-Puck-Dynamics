"""Simplified rink geometry."""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class RinkGeometry:
    length_m: float = 60.96
    width_m: float = 25.91
    net_zone_depth_m: float = 4.0
    glass_height_m: float = 1.2
