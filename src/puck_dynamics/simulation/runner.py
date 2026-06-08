"""Batch simulation runner."""

from __future__ import annotations
import numpy as np
from .engine import SimulationEngine
from .sampler import sample_initial_state


def run_monte_carlo(num_samples: int, seed: int | None = None) -> list[tuple[float, float]]:
    """Run many trajectories and return landing points."""
    rng = np.random.default_rng(seed)
    engine = SimulationEngine()
    landings: list[tuple[float, float]] = []

    for _ in range(num_samples):
        state = sample_initial_state(rng)
        final_state = engine.run(state, rng)
        landings.append((final_state.x, final_state.y))

    return landings
