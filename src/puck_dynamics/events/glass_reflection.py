"""Glass reflection event handling."""

from __future__ import annotations
from ..physics.kinematics import State


def reflect_off_glass(state: State, restitution: float) -> State:
    """Reflect the x-component of velocity at a boundary."""
    return State(
        x=state.x,
        y=state.y,
        vx=-state.vx * restitution,
        vy=state.vy * restitution,
        t=state.t,
        active=state.active,
    )
