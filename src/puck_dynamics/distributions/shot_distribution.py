"""Shot-origin sampling for hockey-specific launch regions."""

from __future__ import annotations
import numpy as np


def sample_shot_origin(rng: np.random.Generator) -> tuple[float, float]:
    """
    Sample a plausible shot origin in rink coordinates.

    This is a placeholder mixture model that can later be replaced with
    empirical shot maps or team-specific shot data.
    """
    region = rng.choice(["slot", "point", "perimeter"], p=[0.5, 0.3, 0.2])

    if region == "slot":
        x = rng.normal(loc=45.0, scale=2.0)
        y = rng.normal(loc=0.0, scale=4.0)
    elif region == "point":
        x = rng.normal(loc=52.0, scale=2.5)
        y = rng.normal(loc=0.0, scale=7.0)
    else:
        x = rng.normal(loc=40.0, scale=4.0)
        y = rng.normal(loc=0.0, scale=11.0)

    return float(x), float(y)
