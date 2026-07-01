from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Tuple

from puck_dynamics.geometry.point import Point3D
from puck_dynamics.geometry.circle import Circle


@dataclass(frozen=True)
class Arc:

    circle: Circle
    start_angle: float
    end_angle: float
    clockwise: bool = False

    def _normalize(self, angle: float) -> float:
        return (angle + 2 * math.pi) % (2 * math.pi)

    def sweep_angle(self) -> float:
        """Unsigned sweep angle of the arc in radians (in [0, 2*pi])."""
        a0 = self._normalize(self.start_angle)
        a1 = self._normalize(self.end_angle)
        if self.clockwise:
            # travel negative direction
            sweep = (a0 - a1) % (2 * math.pi)
        else:
            sweep = (a1 - a0) % (2 * math.pi)
        return sweep

    def length(self) -> float:
        """Arc length (meters, same units as circle.radius)."""
        return self.circle.radius * self.sweep_angle()

    def point_at_fraction(self, t: float) -> Point3D:
    
        if not 0.0 <= t <= 1.0:
            raise ValueError("t must be in [0,1]")
        a0 = self.start_angle
        sweep = self.sweep_angle()
        if self.clockwise:
            angle = a0 - t * sweep
        else:
            angle = a0 + t * sweep
        return self.circle.point_on_circle(angle)

    def contains_point(self, p: Point3D, tol: float = 1e-9) -> bool:

        # check radial equality via circle.distance_to_point (disk distance)
        # point must project to circle rim within tol
        proj_dist = self.circle.distance_to_point(p)
        if proj_dist > tol:
            return False

        # compute angle of projection relative to circle local frame
        # reuse circle internal frame construction by finding closest point on circle center->proj
        proj = self.circle.plane.project_point(p)
        # vector in plane from center to proj
        v = proj - self.circle.center
        if v.norm() == 0.0:
            # ambiguous angle at center; not considered on arc boundary unless radius==0
            return False
        # compute angle using circle.point_on_circle construction: need consistent basis
        # reconstruct same local axes as Circle.point_on_circle
        n = self.circle.unit_normal().to_array()
        import numpy as np
        arb = np.array([1.0, 0.0, 0.0])
        if abs(np.dot(arb, n)) > 0.9:
            arb = np.array([0.0, 1.0, 0.0])
        e1 = np.cross(n, arb)
        e1 = e1 / np.linalg.norm(e1)
        e2 = np.cross(n, e1)

        x = float(np.dot(v.to_array(), e1))
        y = float(np.dot(v.to_array(), e2))
        angle = math.atan2(y, x)
        angle = (angle + 2 * math.pi) % (2 * math.pi)

        a0 = (self.start_angle + 2 * math.pi) % (2 * math.pi)
        a1 = (self.end_angle + 2 * math.pi) % (2 * math.pi)
        if self.clockwise:
            # valid if angle is in descending modular interval [a1, a0]
            if a1 <= a0:
                return a1 - tol <= angle <= a0 + tol
            else:
                return (angle >= 0.0 - tol and angle <= a0 + tol) or (angle >= a1 - tol and angle <= 2 * math.pi + tol)
        else:
            # counter-clockwise: [a0, a1]
            if a0 <= a1:
                return a0 - tol <= angle <= a1 + tol
            else:
                return (angle >= a0 - tol and angle <= 2 * math.pi + tol) or (angle >= 0.0 - tol and angle <= a1 + tol)

