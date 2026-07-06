from __future__ import annotations
from typing import List
from puck_dynamics.arena import Rink
from .constants import DT
from .integrator import step as integrate
from .collision import Collider
from .puck import Puck

class World:

    def __init__(self, rink: Rink | None = None, dt: float = DT):
        self.rink = rink or Rink()
        self.dt = dt
        self.pucks: List[Puck] = []
        self.collider = Collider(list(self.rink.collision_surfaces()))

    def add(self, puck: Puck) -> None:
        self.pucks.append(puck)

    def tick(self) -> None:
        for puck in self.pucks:
            integrate(puck, self.dt)
            self.collider.handle(puck, self.dt)
