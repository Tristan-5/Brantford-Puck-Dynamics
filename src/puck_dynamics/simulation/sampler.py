"""Initial-condition sampling for a puck trajectory."""

from __future__ import annotations
import numpy as np
from ..distributions.shot_distribution import sample_shot_origin
from ..distributions.velocity_distribution import sample_velocity
from ..physics.kinematics import State


def sample_initial_state(rng: np.random.Generator) -> State:
    x, y = sample_shot_origin(rng)
    speed = sample_velocity(rng)
    angle = rng.normal(loc=0.0, scale=np.deg2rad(12.0))
    return State(x=x, y=y, vx=float(speed * np.cos(angle)), vy=float(speed * np.sin(angle)))
