from __future__ import annotations
from dataclasses import dataclass
from puck_dynamics.geometry import Point3D as Vec

# official spec
MASS   = 0.170     # kg
RAD    = 0.0381    # m
I_Z    = 0.5 * MASS * RAD * RAD

@dataclass
class PuckState:
    pos:  Vec
    vel:  Vec
    ω:    Vec        # angular (rad/s) – mostly around Z

@dataclass
class Puck:
    state: PuckState
    mass:  float = MASS
    radius:float = RAD
    moi_z: float = I_Z     # disc about symmetry axis

    # helpers
    @property
    def pos(self) -> Vec: return self.state.pos
    @property
    def vel(self) -> Vec: return self.state.vel
    @property
    def ω(self)   -> Vec: return self.state.ω

