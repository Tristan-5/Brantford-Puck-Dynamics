"""Single-shot simulation engine."""

from __future__ import annotations
import numpy as np
from ..arena.geometry import RinkGeometry
from ..arena.boundaries import check_boundaries
from ..events.absorption import absorb
from ..events.deflection import apply_deflection
from ..events.glass_reflection import reflect_off_glass
from ..physics.kinematics import State, step_state


class SimulationEngine:
    """Run one trajectory through the simplified arena."""

    def __init__(self, geom: RinkGeometry | None = None, dt: float = 0.01):
        self.geom = geom or RinkGeometry()
        self.dt = dt

    def run(self, state: State, rng: np.random.Generator, max_steps: int = 500) -> State:
        current = state
        for _ in range(max_steps):
            if not current.active:
                break

            current = step_state(current, self.dt)
            boundaries = check_boundaries(current.x, current.y, self.geom)

            if boundaries.hit_netting:
                current = absorb(current)
                break

            if boundaries.hit_glass:
                current = reflect_off_glass(current, restitution=0.85)

            if current.x > self.geom.length_m - 8.0 and abs(current.y) < 6.0 and rng.random() < 0.15:
                current = apply_deflection(current, rng)

        return current
