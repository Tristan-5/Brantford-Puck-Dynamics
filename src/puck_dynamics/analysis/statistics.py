"""Basic summary statistics."""

from __future__ import annotations
import numpy as np


def summarize(points: list[tuple[float, float]]) -> dict[str, float]:
    arr = np.asarray(points, dtype=float)
    return {
        "n": float(len(points)),
        "mean_x": float(arr[:, 0].mean()) if len(points) else float("nan"),
        "mean_y": float(arr[:, 1].mean()) if len(points) else float("nan"),
        "std_x": float(arr[:, 0].std()) if len(points) else float("nan"),
        "std_y": float(arr[:, 1].std()) if len(points) else float("nan"),
    }
