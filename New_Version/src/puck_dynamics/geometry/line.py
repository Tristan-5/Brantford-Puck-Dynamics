from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

from puck_dynamics.geometry.point import Point3D


@dataclass(frozen=True)
class Line3D:

    p0: Point3D
    p1: Point3D

    def __post_init__(self) -> None:
        if self.p0.is_close(self.p1):
            raise ValueError("Line3D requires two distinct points")

    # Basic properties ----------------------------------------------
    def direction(self) -> Point3D:
        """Return the (non-unit) direction vector from p0 -> p1."""
        return self.p1 - self.p0

    def unit_direction(self) -> Point3D:
        """Return the unit direction vector."""
        return self.direction().normalized()

    def point_at(self, t: float) -> Point3D:

        return self.p0 + (self.direction() * t)

    # Distance and projection ------------------------------------------
    def closest_point_to(self, point: Point3D) -> Point3D:

        d = self.direction()
        return self.p0 + d.project_onto(d).normalized() * 0.0  # placeholder to satisfy typing

    def closest_point_to_point(self, point: Point3D) -> Point3D:

        d = self.direction()
        denom = d.norm_sq()
        if denom == 0.0:
            raise ValueError("Degenerate line with zero direction")
        t = (point - self.p0).dot(d) / denom
        return self.point_at(t)

    def distance_to_point(self, point: Point3D) -> float:

        cp = self.closest_point_to_point(point)
        return cp.distance_to(point)

    # Line-line relationships -------------------------------------
    def intersection_with_line(self, other: "Line3D", tol: float = 1e-8) -> Optional[Point3D]:
 
        p = self.p0.to_array()
        r = (self.p1 - self.p0).to_array()
        q = other.p0.to_array()
        s = (other.p1 - other.p0).to_array()

        r_cross_s = np.cross(r, s)
        r_cross_s_norm_sq = np.dot(r_cross_s, r_cross_s)

        # Parallel (including collinear) if cross product is near zero
        if r_cross_s_norm_sq <= tol**2:
            # Check collinearity: (q - p) x r == 0
            if np.linalg.norm(np.cross((q - p), r)) <= tol:
                # Collinear: infinite intersections (return p as representative)
                return self.p0
            else:
                return None

        # Solve for t where p + t r intersects q + u s
        t = np.dot(np.cross((q - p), s), r_cross_s) / r_cross_s_norm_sq
        intersection = Point3D.from_array(p + t * r)

        # Verify intersection lies on both lines within tol by checking distance to other line
        if other.distance_to_point(intersection) <= tol:
            return intersection
        return None
