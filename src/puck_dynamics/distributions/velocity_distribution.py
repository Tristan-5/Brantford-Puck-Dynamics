"""Velocity sampling for wrist shots, slapshots, and intermediate cases."""

from __future__ import annotations
import numpy as np


def sample_velocity(rng: np.random.Generator) -> float:
    """Sample a shot speed in meters per second."""
    kind = rng.choice(["wrist", "slap"], p=[0.65, 0.35])
    if kind == "wrist":
        return float(np.clip(rng.normal(loc=28.0, scale=4.0), 15.0, 38.0))
    return float(np.clip(rng.normal(loc=42.0, scale=5.0), 28.0, 55.0))
