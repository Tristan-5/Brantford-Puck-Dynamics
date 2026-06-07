"""Absorption event for netting and terminal out-of-play conditions."""

from __future__ import annotations
from ..physics.kinematics import State


def absorb(state: State) -> State:
    """Mark the puck trajectory as inactive."""
    return State(
        x=state.x,
        y=state.y,
        vx=0.0,
        vy=0.0,
        t=state.t,
        active=False,
    )
