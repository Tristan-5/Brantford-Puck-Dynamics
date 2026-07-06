from __future__ import annotations
from dataclasses import dataclass
import math
import random

from puck_dynamics.geometry import Point3D as Vec
from .distributions import (
    pick_shot_type, sample_release, shot_prior, sample_scalar)

# local ShotSpec identical to physics.shots.ShotSpec
@dataclass(slots=True)
class ShotSpec:
    type: str
    origin: Vec
    speed: float          # m/s
    elev:  float          # deg
    azim:  float          # deg  (shooting direction in rink frame)
    spin:  float          # rev/s

def sample_shot(towards_goal: bool = True) -> ShotSpec:
    stype = pick_shot_type()
    pri   = shot_prior(stype)

    # origin (sampled in attacking half-rink, mirror to defending side
    # 50/50 so we cover both directions without doubling rows)
    x, y = sample_release(stype)
    if not towards_goal and random.random() < 0.5:
        x = -x
        y = -y

    origin = Vec(x, y, 0.15)  # 15 cm off ice (typical release)

    speed = sample_scalar(pri.speed)
    elev  = sample_scalar(pri.elev)
    spin  = sample_scalar(pri.spin)

    # azimuth: small random left/right plus bias toward net centre
    azim = random.gauss(0.0, 4.0)   # deg

    return ShotSpec(stype, origin, speed, elev, azim, spin)
