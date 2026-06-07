"""Deflection event logic for goalie/stick/body interactions."""

from __future__ import annotations
import numpy as np
from ..physics.kinematics import State
from ..distributions.deflection_distribution import sample_deflection


def apply_deflection(state: State, rng: np.random.Generator) -> State:
    """Apply a stochastic deflection to the state velocity."""
    angle_offset, speed_scale = sample_deflection(rng, speed=(state.vx**2 + state.vy**2) ** 0.5)
    speed = (state.vx**2 + state.vy**2) ** 0.5 * speed_scale
    angle = np.arctan2(state.vy, state.vx) + angle_offset
    return State(
        x=state.x,
        y=state.y,
        vx=float(speed * np.cos(angle)),
        vy=float(speed * np.sin(angle)),
        t=state.t,
        active=state.active,
    )
