"""Heatmap generation utilities."""

from __future__ import annotations
import numpy as np


def make_density_grid(points: list[tuple[float, float]], bins: int = 50):
    """Return a 2D histogram and bin edges."""
    xs = np.array([p[0] for p in points], dtype=float)
    ys = np.array([p[1] for p in points], dtype=float)
    return np.histogram2d(xs, ys, bins=bins)
