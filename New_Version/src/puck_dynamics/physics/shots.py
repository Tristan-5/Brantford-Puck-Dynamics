from __future__ import annotations
from dataclasses import dataclass
import math, random
from puck_dynamics.geometry import Point3D as Vec
from .puck import Puck, PuckState

from simulation.shot_sampler import ShotSpec 

@dataclass
class ShotSpec:
    speed: float          # m/s
    elev:  float          # deg
    azim:  float          # deg (0 = straight ahead)
    spin:  float          # rev/s (+ = top-spin wrt +Y)

class ShotFactory:
    @staticmethod
    def from_spec(spec: ShotSpec) -> Puck:
        v   = spec.speed
        elev= math.radians(spec.elev)
        azim= math.radians(spec.azim)

        vx = v * math.cos(elev) * math.cos(azim)
        vy = v * math.cos(elev) * math.sin(azim)
        vz = v * math.sin(elev)

        spin_rad = spec.spin * 2*math.pi
        state = PuckState(spec.origin,
                          Vec(vx, vy, vz),
                          Vec(0, 0, spin_rad))
        return Puck(state)

    # templates
    @classmethod
    def wrist(cls, origin: Vec) -> Puck:
        s = ShotSpec(
            speed=random.uniform(18, 35),     # 65-126 km/h
            elev=random.uniform(1, 10),
            azim=random.uniform(-5, 5),
            spin=random.uniform(8, 15),
        )
        return cls._spawn(s, origin)

    @classmethod
    def slap(cls, origin: Vec) -> Puck:
        s = ShotSpec(
            speed=random.uniform(35, 45),     # 126-162 km/h
            elev=random.uniform(2, 6),
            azim=random.uniform(-3, 3),
            spin=random.uniform(6, 12),
        )
        return cls._spawn(s, origin)

    @classmethod
    def deflection(cls, origin: Vec) -> Puck:
        s = ShotSpec(
            speed=random.uniform(10, 25),
            elev=random.uniform(1, 15),
            azim=random.uniform(-15, 15),
            spin=random.uniform(4, 8),
        )
        return cls._spawn(s, origin)
