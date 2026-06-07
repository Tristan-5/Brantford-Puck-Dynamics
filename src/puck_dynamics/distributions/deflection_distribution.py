"""Deflection perturbations for puck redirection events."""

from __future__ import annotations
import numpy as np


def sample_deflection(rng: np.random.Generator, speed: float) -> tuple[float, float]:
    """
    Return a direction angle offset (radians) and a speed multiplier.

    The returned values are intentionally simple placeholders that can be
    conditioned on deflection type later.
    """
    angle_offset = float(rng.normal(loc=0.0, scale=np.deg2rad(18.0)))
    speed_scale = float(np.clip(rng.normal(loc=0.7, scale=0.12), 0.25, 0.95))
    return angle_offset, speed_scale
