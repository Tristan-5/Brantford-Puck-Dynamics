"""Named rink zones used for shot sampling and reporting."""

from __future__ import annotations

from dataclasses import dataclass

@dataclass
class ShotZone:
    name: str
    center_x: float
    center_y: float
    sigma_x: float
    sigma_y: float
    weight: float

ZONES = {
    "slot": {"x_range": (42.0, 48.0), "y_range": (-6.0, 6.0)},
    "point": {"x_range": (48.0, 56.0), "y_range": (-10.0, 10.0)},
    "perimeter": {"x_range": (35.0, 48.0), "y_range": (-15.0, 15.0)},
}
