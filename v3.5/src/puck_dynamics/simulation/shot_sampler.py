from __future__ import annotations
from dataclasses import dataclass
import math
import random

from puck_dynamics.geometry import Point3D as Vec
from puck_dynamics.arena.dimensions import NHLStandardDimensions
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


@dataclass(frozen=True, slots=True)
class ShotSamplingConfig:
    offensive_weight: float = 0.72
    neutral_weight: float = 0.18
    deflection_weight: float = 0.10
    offensive_azim_sigma_deg: float = 22.0
    neutral_lateral_sigma_deg: float = 12.0
    neutral_forward_sigma_deg: float = 30.0
    deflection_lateral_sigma_deg: float = 16.0
    deflection_forward_sigma_deg: float = 20.0


DEFAULT_SHOT_CONFIG = ShotSamplingConfig()

def sample_shot(towards_goal: bool = True,
                config: ShotSamplingConfig | None = None) -> ShotSpec:
    cfg = config or DEFAULT_SHOT_CONFIG
    stype = pick_shot_type()
    pri   = shot_prior(stype)

    dims = NHLStandardDimensions()
    half_len = dims.length / 2.0
    half_wid = dims.width / 2.0

    # Mixture model: offensive-zone shots are most common, neutral-zone plays
    # are less common and weaker, and true neutral-zone deflections are the
    # rarest. This keeps center-ice attempts from dominating the sample.
    side = -1.0 if random.random() < 0.5 else 1.0
    zone = random.choices(
        ("offensive", "neutral", "deflection"),
        weights=(cfg.offensive_weight, cfg.neutral_weight, cfg.deflection_weight),
    )[0]

    if zone == "offensive":
        x = side * random.uniform(0.64 * half_len, half_len + 5.0)
        y = random.gauss(0.0, half_wid / 3.6)
        speed_scale = random.uniform(1.06, 1.22)
        elev_shift = random.uniform(0.0, 1.0)
    elif zone == "neutral":
        x = random.gauss(0.0, half_len / 8.0)
        x = min(max(x, -0.22 * half_len), 0.22 * half_len)
        y = random.gauss(0.0, half_wid / 2.4)
        speed_scale = random.uniform(0.74, 0.90)
        elev_shift = random.uniform(-1.0, 0.2)
    else:
        x = side * random.uniform(0.14 * half_len, 0.68 * half_len)
        y = random.gauss(0.0, half_wid / 2.0)
        if random.random() < 0.35:
            y = random.uniform(-half_wid - 4.0, half_wid + 4.0)
        speed_scale = random.uniform(0.84, 0.98)
        elev_shift = random.uniform(-0.6, 0.6)

    x = min(max(x, -half_len - 10.0), half_len + 10.0)
    y = min(max(y, -half_wid - 8.0), half_wid + 8.0)

    if not towards_goal and random.random() < 0.5:
        x = -x
        y = -y

    origin = Vec(x, y, 0.15)  # 15 cm off ice (typical release)

    speed = sample_scalar(pri.speed) * speed_scale
    elev  = sample_scalar(pri.elev) + elev_shift
    spin  = sample_scalar(pri.spin)

    # Offensive-zone shots still prefer down-rink travel; neutral-zone plays
    # are more lateral and less forceful.
    if zone == "neutral":
        if random.random() < 0.78:
            azim = random.gauss(
                90.0 if random.random() < 0.5 else -90.0,
                cfg.neutral_lateral_sigma_deg,
            )
        else:
            azim = random.gauss(
                0.0 if side < 0.0 else 180.0,
                cfg.neutral_forward_sigma_deg,
            )
    elif zone == "deflection":
        if random.random() < 0.60:
            azim = random.gauss(
                90.0 if random.random() < 0.5 else -90.0,
                cfg.deflection_lateral_sigma_deg,
            )
        else:
            azim = random.gauss(
                0.0 if side < 0.0 else 180.0,
                cfg.deflection_forward_sigma_deg,
            )
    else:
        if side < 0.0:
            azim = random.gauss(0.0, cfg.offensive_azim_sigma_deg)   # left end -> shot to the right
        else:
            azim = random.gauss(180.0, cfg.offensive_azim_sigma_deg) # right end -> shot to the left

    return ShotSpec(stype, origin, speed, elev, azim, spin)
