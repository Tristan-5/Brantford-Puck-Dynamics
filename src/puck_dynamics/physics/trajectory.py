"""Trajectory propagation helpers."""

from __future__ import annotations
from .kinematics import State, step_state


def propagate(state: State, dt: float, steps: int) -> State:
    """Propagate a state forward for a fixed number of steps."""
    current = state
    for _ in range(steps):
        if not current.active:
            break
        current = step_state(current, dt)
    return current
