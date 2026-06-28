"""
geometry.py

Core geometric definitions for hockey arenas.

This module contains immutable geometric data structures used
throughout the puck dynamics package.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ArenaDimensions:
    """
    Standard geometric dimensions of a hockey rink.

    All dimensions are expressed in metres.
    """

    rink_length: float = 60.96
    rink_width: float = 25.90

    offensive_zone_start: float = 35.00

    goal_line_x: float = 60.00

    board_height: float = 1.22
    glass_height: float = 2.44

    goal_width: float = 1.83
    goal_depth: float = 1.12

    crease_radius: float = 1.83

    corner_radius: float = 8.50

    blue_line_x: float = 35.00

    faceoff_circle_radius: float = 4.57

    faceoff_spot_radius: float = 0.15

    neutral_zone_length: float = 15.24


@dataclass(frozen=True, slots=True)
class GoalGeometry:
    """
    Geometry of the goal.
    """

    x: float
    y: float

    width: float
    depth: float


@dataclass(frozen=True, slots=True)
class CircleGeometry:
    """
    Generic circle.
    """

    x: float
    y: float

    radius: float


@dataclass(frozen=True, slots=True)
class RectangleGeometry:
    """
    Axis-aligned rectangle.
    """

    xmin: float
    xmax: float

    ymin: float
    ymax: float


@dataclass(frozen=True, slots=True)
class LineGeometry:
    """
    Straight line segment.
    """

    x1: float
    y1: float

    x2: float
    y2: float


class OffensiveZone:
    """
    Geometric description of the offensive zone.

    This object provides reusable geometric primitives for
    plotting and collision detection.
    """

    def __init__(self, dims: ArenaDimensions | None = None):

        self.dims = dims or ArenaDimensions()

        self.goal = GoalGeometry(
            x=self.dims.goal_line_x,
            y=self.dims.rink_width / 2,
            width=self.dims.goal_width,
            depth=self.dims.goal_depth,
        )

        self.left_faceoff = CircleGeometry(
            x=54.86,
            y=6.70,
            radius=self.dims.faceoff_circle_radius,
        )

        self.right_faceoff = CircleGeometry(
            x=54.86,
            y=19.20,
            radius=self.dims.faceoff_circle_radius,
        )

        self.blue_line = LineGeometry(
            self.dims.blue_line_x,
            0.0,
            self.dims.blue_line_x,
            self.dims.rink_width,
        )

        self.bounds = RectangleGeometry(
            xmin=self.dims.offensive_zone_start,
            xmax=self.dims.rink_length,
            ymin=0.0,
            ymax=self.dims.rink_width,
        )

    @property
    def goal_center(self) -> tuple[float, float]:
        """
        Return goal centre coordinates.
        """
        return (
            self.goal.x,
            self.goal.y,
        )

    @property
    def rink_center(self) -> tuple[float, float]:
        """
        Return centre of the offensive zone.
        """
        return (
            (
                self.bounds.xmin +
                self.bounds.xmax
            )
            / 2,
            self.dims.rink_width / 2,
        )

    @property
    def width(self) -> float:
        return self.dims.rink_width

    @property
    def length(self) -> float:
        return (
            self.bounds.xmax -
            self.bounds.xmin
        )
