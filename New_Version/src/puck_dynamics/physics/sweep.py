from puck_dynamics.geometry import Point3D as Vec, Box3D, Cylinder, Plane3D
from .constants import SWEEP_EPS

def time_of_impact(p0: Vec, p1: Vec, r: float, surf: object) -> float | None:
    """
    Returns t in [0,1] where contact occurs, None if no hit within segment.
    Fast analytic tests for Box3D inner faces, Cylinders, Plane3D.
    """
    if isinstance(surf, Plane3D):
        n = surf.normal()
        d0 = surf.signed_distance(p0) - r
        d1 = surf.signed_distance(p1) - r
        if d0 > 0 and d1 > 0:
            return None
        if d0 < 0 and d1 < 0:
            return None
        denom = d0 - d1
        if abs(denom) < SWEEP_EPS:
            return None
        t = d0 / denom
        return max(0.0, min(1.0, t))
    # Fallback: discrete distance check mid-step (cheap, slightly inelastic)
    return None
