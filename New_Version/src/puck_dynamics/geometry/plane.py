from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

from puck_dynamics.geometry.point import Point3D
from puck_dynamics.geometry.line import Line3D


@dataclass(frozen=True)
class Plane:

    point: Point3D
    normal: Point3D

    def __post_init__(self) -> None:
        if self.normal.norm_sq() == 0.0:
            raise ValueError("Plane normal cannot be the zero vector")

    # Construction helpers -----------------------------------------------
    @classmethod
    def from_point_and_normal(cls, point: Point3D, normal: Point3D) -> "Plane":
        """Create a plane from point and normal."""
        return cls(point, normal)

    @classmethod
    def from_three_points(cls, a: Point3D, b: Point3D, c: Point3D) -> "Plane":

        ab = b - a
        ac = c - a
        n = ab.cross(ac)
        if n.norm_sq() == 0.0:
            raise ValueError("Points are collinear; cannot define a plane")
        return cls(a, n)

    # Properties ------------------------------------------------
    def unit_normal(self) -> Point3D:
        """Return unit-length normal vector."""
        return self.normal.normalized()

    # Distance / projection --------------------------------------------
    def signed_distance(self, p: Point3D) -> float:

        vec = p - self.point
        return vec.dot(self.unit_normal())

    def distance(self, p: Point3D) -> float:
        """Unsigned perpendicular distance."""
        return abs(self.signed_distance(p))

    def project_point(self, p: Point3D) -> Point3D:
        """
        Orthogonal projection of point `p` onto the plane.
        """
        d = self.signed_distance(p)
        return p - self.unit_normal() * d

    # Relationships with lines --------------------------------------------
    def intersect_line(self, line: Line3D, tol: float = 1e-10) -> Optional[Point3D]:

        p0 = line.p0
        r = line.direction()
        denom = self.normal.dot(r)
        if abs(denom) <= tol:
            # Parallel: either contained or no intersection
            if abs(self.signed_distance(p0)) <= tol:
                return line.p0  # representative point
            return None
        t = self.normal.dot(self.point - p0) / denom
        return line.point_at(t)

    # Plane-plane intersection -------------------------------------------
    def intersection_with_plane(self, other: "Plane", tol: float = 1e-10) -> Optional[Line3D]:

        n1 = self.normal.to_array()
        n2 = other.normal.to_array()
        dir_cross = np.cross(n1, n2)
        if np.linalg.norm(dir_cross) <= tol:
            # Normals are parallel -> planes parallel or coincident
            # Check if points satisfy same plane equation
            if abs(self.signed_distance(other.point)) <= tol:
                # Coincident: return a representative line (choose direction orthogonal to normal)
                # find a direction vector orthogonal to the normal
                normal = self.unit_normal()
                # pick an arbitrary vector not parallel to normal
                arb = Point3D(1.0, 0.0, 0.0)
                if abs(normal.dot(arb)) > 0.9:
                    arb = Point3D(0.0, 1.0, 0.0)
                direction = normal.cross(arb)
                return Line3D(self.point, self.point + direction)
            return None
        # For non-parallel planes, compute a point on the intersection line.
        # Solve for point x satisfying: x = p0 + alpha * n1 + beta * n2, with x · n1 = d1, x · n2 = d2
        # Use linear system on alpha,beta.
        A = np.vstack([n1, n2]).T  # 3x2
        d = np.array([self.normal.dot(self.point), other.normal.dot(other.point)])
        # least squares to find coefficients in the span of n1,n2 that yield x
        coeffs, *_ = np.linalg.lstsq(A, d, rcond=None)
        alpha, beta = float(coeffs[0]), float(coeffs[1])
        point_on_line = Point3D.from_array(alpha * n1 + beta * n2)
        direction = Point3D.from_array(dir_cross)
        return Line3D(point_on_line, point_on_line + direction)

    # Vector reflection ------------------------------------------------
    def reflect_vector(self, v: Point3D) -> Point3D:
        """
        Reflect vector `v` about the plane (mirror reflection).

        Returns the reflected vector (not translating any point).
        """
        n = self.unit_normal()
        return v - n * (2.0 * v.dot(n))
