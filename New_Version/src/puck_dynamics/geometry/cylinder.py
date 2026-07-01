from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Optional

import numpy as np

from puck_dynamics.geometry.point import Point3D
from puck_dynamics.geometry.line import Line3D


@dataclass(frozen=True)
class Cylinder:

    base_center: Point3D
    axis: Point3D
    height: float
    radius: float

    def __post_init__(self) -> None:
        if self.height < 0.0:
            raise ValueError("height must be non-negative")
        if self.radius < 0.0:
            raise ValueError("radius must be non-negative")
        if self.axis.norm_sq() == 0.0 and self.height > 0.0:
            raise ValueError("axis cannot be zero vector when height > 0")

    @property
    def unit_axis(self) -> Point3D:
        if self.height == 0.0:
            # axis irrelevant when height zero; return arbitrary unit
            return Point3D.unit_z()
        return self.axis.normalized()

    @property
    def top_center(self) -> Point3D:
        """Center point of the top circular face."""
        return self.base_center + self.unit_axis * self.height

    # Point classification ------------------------------------------
    def contains(self, p: Point3D, tol: float = 1e-12) -> bool:
        """
        Return True if point lies within the closed cylinder (including caps).
        """
        # compute axial coordinate
        v = p - self.base_center
        z = v.dot(self.unit_axis)
        if z < -tol or z > self.height + tol:
            return False
        # radial distance to axis
        proj = self.base_center + self.unit_axis * z
        r = proj.distance_to(p)
        return r <= self.radius + tol

    def axial_and_radial_coords(self, p: Point3D) -> Tuple[float, float]:

        v = p - self.base_center
        z = v.dot(self.unit_axis)
        proj = self.base_center + self.unit_axis * z
        r = proj.distance_to(p)
        return z, r

    def closest_point(self, p: Point3D) -> Point3D:

        z, r = self.axial_and_radial_coords(p)

        # clamp axial coordinate to [0, height]
        z_clamped = min(max(z, 0.0), self.height)
        proj = self.base_center + self.unit_axis * z_clamped

        if r <= self.radius:
            # point is above/below caps or inside radial extent: clamp to cap if outside axial
            if 0.0 <= z <= self.height:
                return p  # inside cylinder
            else:
                # nearest point lies on cap disk at z_clamped, at same radial direction
                return proj + (p - proj).normalized() * min(r, self.radius) if r != 0.0 else proj
        else:
            # nearest point lies on curved surface at clamped z
            radial_dir = (p - proj).normalized()
            return proj + radial_dir * self.radius

    def distance_to_point(self, p: Point3D) -> float:
        """Euclidean distance from point p to closed cylinder (0 if inside)."""
        cp = self.closest_point(p)
        return cp.distance_to(p)

    # Line intersection -----------------------------
    def intersect_line(self, line: Line3D, tol: float = 1e-12) -> Tuple[bool, Optional[Tuple[Point3D, Point3D]]]:

        # Transform to cylinder-local coordinates where axis is z-axis and base_center is origin.
        u = self.unit_axis.to_array()
        # build orthonormal basis: u, e1, e2
        # choose arbitrary vector not parallel to u
        arb = np.array([1.0, 0.0, 0.0])
        if abs(np.dot(arb, u)) > 0.9:
            arb = np.array([0.0, 1.0, 0.0])
        e1 = np.cross(u, arb)
        e1 /= np.linalg.norm(e1)
        e2 = np.cross(u, e1)

        def to_local(pt: Point3D) -> np.ndarray:
            v = pt.to_array() - self.base_center.to_array()
            return np.array([np.dot(v, e1), np.dot(v, e2), np.dot(v, u)])

        p0 = to_local(line.p0)
        d = (line.direction()).to_array()
        # local direction
        d_local = np.array([np.dot(d, e1), np.dot(d, e2), np.dot(d, u)])

        # Solve quadratic for intersection with infinite cylinder x^2 + y^2 = r^2
        a = d_local[0]**2 + d_local[1]**2
        b = 2.0 * (p0[0]*d_local[0] + p0[1]*d_local[1])
        c = p0[0]**2 + p0[1]**2 - self.radius**2

        ts = []
        if abs(a) > tol:
            disc = b*b - 4*a*c
            if disc >= 0.0:
                sqrt_disc = np.sqrt(disc)
                t1 = (-b - sqrt_disc) / (2*a)
                t2 = (-b + sqrt_disc) / (2*a)
                for t in (t1, t2):
                    z = p0[2] + t * d_local[2]
                    if -tol <= z <= self.height + tol:
                        ts.append(t)
        else:
            # line parallel to cylinder axis in xy -> no side intersections; could hit caps
            pass

        # Check intersections with caps (disks at z=0 and z=height)
        if abs(d_local[2]) > tol:
            for z_cap in (0.0, self.height):
                t_cap = (z_cap - p0[2]) / d_local[2]
                x = p0[0] + t_cap * d_local[0]
                y = p0[1] + t_cap * d_local[1]
                if x*x + y*y <= self.radius**2 + tol:
                    ts.append(t_cap)

        if not ts:
            return False, None

        ts_sorted = sorted(set(ts))
        if len(ts_sorted) == 1:
            p = line.point_at(ts_sorted[0])
            return True, (p, p)
        elif len(ts_sorted) >= 2:
            p_enter = line.point_at(ts_sorted[0])
            p_exit = line.point_at(ts_sorted[-1])
            return True, (p_enter, p_exit)
        return False, None

