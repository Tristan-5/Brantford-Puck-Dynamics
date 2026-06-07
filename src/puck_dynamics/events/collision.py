"""Generic collision handler."""

from __future__ import annotations


def reflect_velocity(vx: float, vy: float, restitution: float = 1.0) -> tuple[float, float]:
    """Reflect a velocity vector with a simple restitution coefficient."""
    return -vx * restitution, vy * restitution
