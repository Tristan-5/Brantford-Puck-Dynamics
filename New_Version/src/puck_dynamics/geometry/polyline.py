from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional

import numpy as np

from puck_dynamics.geometry.point import Point3D


@dataclass(frozen=True)
class Polyline3D:

    points: Tuple[Point3D, ...]

    def __init__(self, points: List[Point3D]):
        if len(points) < 2:
            raise ValueError("Polyline3D requires at least two points")
        object.__setattr__(self, "points", tuple(points))

    # Basic properties ---------------------------------------------------------
    def num_vertices(self) -> int:
        return len(self.points)

    def segments(self) -> List[Tuple[Point3D, Point3D]]:
        """Return list of (p0, p1) segments."""
        return [(self.points[i], self.points[i+1]) for i in range(len(self.points) - 1)]

    def segment_lengths(self) -> List[float]:
        return [p0.distance_to(p1) for p0, p1 in self.segments()]

    def length(self) -> float:
        """Total polyline length."""
        return sum(self.segment_lengths())

    # Parametric sampling --------------------------------
    def point_at_fraction(self, t: float) -> Point3D:
        """
        Return point along polyline at fraction t in [0,1]. Linear interpolation
        along segments using arc-length parameterization.
        """
        if not 0.0 <= t <= 1.0:
            raise ValueError("t must be in [0,1]")
        total = self.length()
        if total == 0.0:
            return self.points[0]
        target = t * total
        acc = 0.0
        for (p0, p1), seg_len in zip(self.segments(), self.segment_lengths()):
            if acc + seg_len >= target or seg_len == 0.0:
                local_t = 0.0 if seg_len == 0.0 else (target - acc) / seg_len
                return p0.lerp(p1, local_t)
            acc += seg_len
        # numerically may reach end
        return self.points[-1]

    # Closest point to external point --------------------------------
    def closest_point(self, p: Point3D) -> Tuple[Point3D, int, float]:
        """
        Find closest point on the polyline to point `p`.

        Returns
        -------
        (closest_point, segment_index, t_on_segment)
            closest_point : Point3D
            segment_index : int   index of segment containing the closest point (0-based)
            t_on_segment : float  parametric position along that segment in [0,1]
        """
        best_dist = float("inf")
        best_point: Optional[Point3D] = None
        best_idx = -1
        best_t = 0.0

        for idx, (p0, p1) in enumerate(self.segments()):
            v = p1 - p0
            w = p - p0
            denom = v.norm_sq()
            if denom == 0.0:
                t = 0.0
                proj = p0
            else:
                t = max(0.0, min(1.0, w.dot(v) / denom))
                proj = p0.lerp(p1, t)
            d = proj.distance_to(p)
            if d < best_dist:
                best_dist = d
                best_point = proj
                best_idx = idx
                best_t = t

        assert best_point is not None
        return best_point, best_idx, best_t

    # Utility -------------------------------------------------------------
    def to_numpy(self) -> np.ndarray:
        """Return vertices as an (N,3) numpy array."""
        return np.vstack([pt.to_array() for pt in self.points])

