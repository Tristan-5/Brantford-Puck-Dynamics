from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Tuple, Optional

import numpy as np

from puck_dynamics.geometry.point import Point3D
from puck_dynamics.geometry.plane import Plane
from puck_dynamics.geometry.line import Line3D


@dataclass(frozen=True)
class Circle:
    """
    Circle in 3D defined by a center point, a plane normal, and a radius.

    Parameters
    ----------
    center : Point3D
        Center of the circle.
    normal : Point3D
        Normal vector of the circle's plane (need not be unit).
    radius : float
        Radius (>= 0).
    """
    center: Point3D
    normal: Point3D
    radius: float

    def __post_init__(self) -> None:
        if self.radius < 0.0:
            raise ValueError("radius must be non-negative")
        if self.normal.norm_sq() == 0.0 and self.radius > 0.0:
            raise ValueError("normal cannot be zero vector when radius > 0")

    @property
    def plane(self) -> Plane:
        """Underlying plane containing the circle."""
        return Plane.from_point_and_normal(self.center, self.normal)

    def unit_normal(self) -> Point3D:
        """Unit normal vector."""
        return self.normal.normalized()

    def point_on_circle(self, angle_rad: float) -> Point3D:
        """
        Return a Point3D on the circle corresponding to angle (radians).
        Angle is measured in an arbitrary local frame; the frame is constructed
        from the circle normal and a chosen orthogonal basis.
        """
        n = self.unit_normal().to_array()
        # choose arbitrary axis not parallel to normal
        arb = np.array([1.0, 0.0, 0.0])
        if abs(np.dot(arb, n)) > 0.9:
            arb = np.array([0.0, 1.0, 0.0])
        e1 = np.cross(n, arb)
        e1 = e1 / np.linalg.norm(e1)
        e2 = np.cross(n, e1)
        p = self.center.to_array() + self.radius * (math.cos(angle_rad) * e1 + math.sin(angle_rad) * e2)
        return Point3D.from_array(p)

    def contains(self, p: Point3D, tol: float = 1e-9) -> bool:
        """
        Return True if point p lies on the disk bounded by the circle (within tolerance).
        """
        # check distance to plane
        if abs(self.plane.signed_distance(p)) > tol:
            return False
        # radial distance in-plane
        r = self.center.distance_to(p)
        return r <= self.radius + tol

    def distance_to_point(self, p: Point3D) -> float:
        """
        Euclidean distance from point p to the circular disk (0 if inside).
        """
        proj = self.plane.project_point(p)
        radial = proj.distance_to(self.center)
        if radial <= self.radius:
            return abs(self.plane.signed_distance(p))
        else:
            # distance to circle boundary (in plane) or to rim in 3D
            rim = Point3D.from_array(self.center.to_array() + (proj.to_array() - self.center.to_array()) * (self.radius / radial))
            # rim may coincide if radial==0
            return p.distance_to(rim)

    def intersect_line(self, line: Line3D, tol: float = 1e-10) -> Optional[Tuple[Point3D, ...]]:
        """
        Intersect an infinite line with the circular disk.

        Returns a tuple of intersection points (0, 1, or 2 points).
        """
        inter = self.plane.intersect_line(line, tol=tol)
        if inter is None:
            return None
        # If the line lies in the plane, return points on line within circle (infinite). Represent as None.
        if inter.is_close(line.p0):
            # line is contained in the plane; compute parametric intersections with circle
            # Project to local 2D by constructing basis and solving quadratic.
            # For simplicity, return None to indicate infinite intersections in-plane.
            return None

        # single intersection point
        p = inter
        if self.center.distance_to(p) <= self.radius + tol:
            return (p,)
        return None

