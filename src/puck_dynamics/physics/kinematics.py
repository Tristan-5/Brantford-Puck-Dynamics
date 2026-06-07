"""Basic kinematic updates for 2D/2.5D puck motion."""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class State:
    x: float
    y: float
    vx: float
    vy: float
    t: float = 0.0
    active: bool = True


def step_state(state: State, dt: float, ax: float = 0.0, ay: float = 0.0) -> State:
    """Advance the state by one time step."""
    x = state.x + state.vx * dt + 0.5 * ax * dt * dt
    y = state.y + state.vy * dt + 0.5 * ay * dt * dt
    vx = state.vx + ax * dt
    vy = state.vy + ay * dt
    return State(x=x, y=y, vx=vx, vy=vy, t=state.t + dt, active=state.active)
