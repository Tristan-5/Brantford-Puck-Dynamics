from __future__ import annotations

from typing import Tuple

Color = Tuple[float, float, float, float]

ICE_BLUE: Color = (0.800, 0.880, 0.960, 1.0)
LINE_RED: Color = (0.863, 0.118, 0.149, 1.0)
LINE_BLUE: Color = (0.047, 0.204, 0.643, 1.0)
GOAL_POST_RED: Color = (0.882, 0.000, 0.094, 1.0)
BOARD_YELLOW: Color = (0.980, 0.824, 0.000, 1.0)
GLASS_TINT: Color = (0.820, 0.930, 0.970, 0.2)
SEAT_GREY: Color = (0.450, 0.450, 0.450, 1.0)

__all__ = [
    "Color",
    "ICE_BLUE",
    "LINE_RED",
    "LINE_BLUE",
    "GOAL_POST_RED",
    "BOARD_YELLOW",
    "GLASS_TINT",
    "SEAT_GREY",
]

