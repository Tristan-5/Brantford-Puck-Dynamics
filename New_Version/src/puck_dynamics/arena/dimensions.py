"""
Authority for all rink and arena dimensions.

Internally values are stored in metres.  Helper functions convert to and
from imperial units to accommodate NHL specifications that are officially
stated in feet and inches.
"""

from __future__ import annotations

from dataclasses import dataclass

FT_TO_M = 0.3048
IN_TO_M = 0.0254

__all__ = ["ft_to_m", "in_to_m", "m_to_ft", "m_to_in", "NHLStandardDimensions"]


def ft_to_m(value_ft: float) -> float:
    """Feet → metres."""
    return value_ft * FT_TO_M


def in_to_m(value_in: float) -> float:
    """Inches → metres."""
    return value_in * IN_TO_M


def m_to_ft(value_m: float) -> float:
    """Metres → feet."""
    return value_m / FT_TO_M


def m_to_in(value_m: float) -> float:
    """Metres → inches."""
    return value_m / IN_TO_M


@dataclass(frozen=True, slots=True)
class NHLStandardDimensions:
    """
    Official NHL rink layout (Rule 1.2).

    All values are stored in metres as floats; convert on demand for
    display purposes.

    Notes
    • The NHL permits ±1 ft tolerance on rink length; we adopt the nominal
      200 ft × 85 ft rectangle.
    • Radii follow the 28 ft corner rule introduced in 1996.
    """

    length: float = ft_to_m(200)           # 60.96 m
    width: float = ft_to_m(85)             # 25.91 m
    corner_radius: float = ft_to_m(28)     # 8.5344 m
    blue_line_distance: float = ft_to_m(64)  # from end boards to near edge
    goal_line_distance: float = ft_to_m(11)  # from end boards to goal line
    goal_crease_radius: float = ft_to_m(6) / 2.0  # 6 ft diameter
    # Heights
    board_height: float = in_to_m(42)      # 3.5 ft
    glass_height: float = ft_to_m(8)       # nominal
    # Seating & safety
    safety_net_height: float = ft_to_m(30)  # above glass

    def rink_aabb(self):
        return self.length / 2.0, self.width / 2.0

