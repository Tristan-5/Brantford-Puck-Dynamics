from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple

import numpy as np

from puck_dynamics.geometry.point import Point3D
from puck_dynamics.geometry.line import Line3D


@dataclass(frozen=True)
class AABB:

    min_pt: Point3D
    max_pt: Point3D

    def __post_init__(self) -> None:
        if (self.min_pt.x > self.max_pt.x
                or self.min_pt.y > self.max_pt.y
                or self.min_pt.z > self.max_pt.z):
            raise ValueError("min_pt must be component-wise <= max_pt")

    @classmethod
    def from_center_halfsizes(cls, center: Point3D, half_sizes: Tuple[float, float, float]) -> "AABB":
        hx, hy, hz = half_sizes
        min_pt = Point3D(center.x - hx, center.y - hy, center.z - hz)
        max_pt = Point3D(center.x + hx, center.y + hy, center.z + hz)
        return cls(min_pt, max_pt)

    def contains(self, p: Point3D, tol: float = 0.0) -> bool:
        return (self.min_pt.x - tol <= p.x <= self.max_pt.x + tol
                and self.min_pt.y - tol <= p.y <= self.max_pt.y + tol
                and self.min_pt.z - tol <= p.z <= self.max_pt.z + tol)

    def closest_point(self, p: Point3D) -> Point3D:
        """Compute closest point on (or inside) the box to p."""
        x = min(max(p.x, self.min_pt.x), self.max_pt.x)
        y = min(max(p.y, self.min_pt.y), self.max_pt.y)
        z = min(max(p.z, self.min_pt.z), self.max_pt.z)
        return Point3D(x, y, z)

    def distance_to_point(self, p: Point3D) -> float:
        """Euclidean distance from p to the box (0 if inside)."""
        cp = self.closest_point(p)
        return cp.distance_to(p)

    def intersect_line(self, line: Line3D, tol: float = 1e-12) -> Tuple[bool, Tuple[Point3D, Point3D]]:

        p = line.p0.to_array()
        d = line.direction().to_array()
        tmin = -np.inf
        tmax = np.inf
        bounds = np.array([self.min_pt.to_array(), self.max_pt.to_array()])  # 2x3

        for i in range(3):
            if abs(d[i]) < tol:
                # Line parallel to slab; must be within slab
                if p[i] < bounds[0, i] - tol or p[i] > bounds[1, i] + tol:
                    return False, (Point3D(0, 0, 0), Point3D(0, 0, 0))
                else:
                    continue
            t1 = (bounds[0, i] - p[i]) / d[i]
            t2 = (bounds[1, i] - p[i]) / d[i]
            t_near = min(t1, t2)
            t_far = max(t1, t2)
            tmin = max(tmin, t_near)
            tmax = min(tmax, t_far)
            if tmin > tmax:
                return False, (Point3D(0, 0, 0), Point3D(0, 0, 0))

        p_enter = line.point_at(tmin)
        p_exit = line.point_at(tmax)
        return True, (p_enter, p_exit)

