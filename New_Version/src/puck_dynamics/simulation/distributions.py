from __future__ import annotations
from dataclasses import dataclass
import random
import bisect
import math
from typing import List, Tuple

Vec2 = Tuple[float, float]

@dataclass(frozen=True, slots=True)
class Gaussian2D:
    weight: float
    mean:   Vec2
    cov:    Vec2  # σ_x, σ_y  (assume axis-aligned – good enough)

    def sample(self) -> Vec2:
        x = random.gauss(self.mean[0], self.cov[0])
        y = random.gauss(self.mean[1], self.cov[1])
        return x, y


@dataclass(frozen=True, slots=True)
class ScalarCDF:
    xs: Tuple[float, ...]
    cdf: Tuple[float, ...]      # same length, last = 1.0

    def sample(self) -> float:
        u = random.random()
        idx = bisect.bisect_left(self.cdf, u)
        if idx == 0:
            return self.xs[0]
        x0, x1 = self.xs[idx-1], self.xs[idx]
        c0, c1 = self.cdf[idx-1], self.cdf[idx]
        # linear interpolate
        t = (u - c0) / (c1 - c0)
        return x0 + t * (x1 - x0)


@dataclass(frozen=True, slots=True)
class ShotPrior:
    gaussians: Tuple[Gaussian2D, ...]
    speed:     ScalarCDF
    elev:      ScalarCDF
    spin:      ScalarCDF


def _cdf_from_hist(edges: List[float], counts: List[int]) -> ScalarCDF:
    total = float(sum(counts))
    cum, xs, cdf = 0.0, [], []
    for e0, e1, n in zip(edges[:-1], edges[1:], counts):
        cum += n / total
        xs.append((e0 + e1)/2)
        cdf.append(min(cum, 1.0))
    return ScalarCDF(tuple(xs), tuple(cdf))

# Numbers below are rounded fits (m)  ———————————

_PRIORS: dict[str, ShotPrior] = {
    "wrist": ShotPrior(
        gaussians=(
            Gaussian2D(0.32, ( 8.8,  0.0), (3.2, 2.5)),   # high slot
            Gaussian2D(0.25, ( 4.0,  1.0), (2.5, 1.8)),   # inner slot L
            Gaussian2D(0.25, ( 4.0, -1.0), (2.5, 1.8)),   # inner slot R
            Gaussian2D(0.18, (12.0,  3.0), (2.0, 1.5)),   # circles L
        ),
        speed=_cdf_from_hist(
            [18, 22, 26, 30, 34, 38], [5, 22, 38, 25, 8]),  # m/s
        elev=_cdf_from_hist(
            [0, 4, 8, 12, 16, 20], [15, 40, 30, 12, 3]),
        spin=_cdf_from_hist(
            [4, 6, 8, 10, 12, 14], [10, 25, 35, 22, 8]),
    ),

    "slap": ShotPrior(
        gaussians=(
            Gaussian2D(0.45, (16.0,  0.0), (4.0, 3.0)),  # point
            Gaussian2D(0.35, (13.0,  3.5), (3.0, 2.0)),  # left circle top
            Gaussian2D(0.20, (13.0, -3.5), (3.0, 2.0)),  # right circle top
        ),
        speed=_cdf_from_hist(
            [30, 34, 38, 42, 46], [12, 38, 34, 14]),
        elev=_cdf_from_hist(
            [1, 3, 5, 7, 9], [20, 40, 28, 12]),
        spin=_cdf_from_hist(
            [2, 4, 6, 8, 10], [12, 34, 32, 22]),
    ),

    "snapshot": ShotPrior(
        gaussians=(
            Gaussian2D(0.4, ( 9.0,  1.5), (3.0, 2.0)),
            Gaussian2D(0.4, ( 9.0, -1.5), (3.0, 2.0)),
            Gaussian2D(0.2, ( 5.0,  0.0), (2.8, 2.3)),
        ),
        speed=_cdf_from_hist(
            [22, 26, 30, 34, 38], [10, 32, 38, 20]),
        elev=_cdf_from_hist(
            [1, 5, 9, 13, 17], [18, 40, 30, 12]),
        spin=_cdf_from_hist(
            [6, 8, 10, 12, 14], [10, 30, 36, 24]),
    ),

    "backhand": ShotPrior(
        gaussians=(
            Gaussian2D(0.6, ( 6.5,  0.5), (2.5, 2.0)),
            Gaussian2D(0.4, ( 3.5, -0.5), (2.0, 1.8)),
        ),
        speed=_cdf_from_hist(
            [16, 20, 24, 28, 32], [18, 36, 30, 16]),
        elev=_cdf_from_hist(
            [2, 6, 10, 14, 18], [16, 38, 32, 14]),
        spin=_cdf_from_hist(
            [3, 5, 7, 9, 11], [15, 35, 32, 18]),
    ),

    "tip": ShotPrior(   # includes deflections and tip-ins
        gaussians=(
            Gaussian2D(0.55, ( 2.0,  0.2), (1.5, 1.2)),
            Gaussian2D(0.45, ( 2.0, -0.2), (1.5, 1.2)),
        ),
        speed=_cdf_from_hist(
            [ 8, 12, 16, 20, 24], [25, 40, 23, 10]),
        elev=_cdf_from_hist(
            [0, 5, 10, 15, 20], [22, 46, 24, 8]),
        spin=_cdf_from_hist(
            [1, 3, 5, 7, 9], [28, 40, 24, 8]),
    ),
}

# league-wide shot-type prior (5-on-5, empty-net filtered)
_TYPE_PRIOR: list[tuple[str, float]] = [
    ("wrist", 0.46),
    ("slap",  0.12),
    ("snapshot", 0.18),
    ("backhand", 0.09),
    ("tip", 0.15),
]
_type_cumsum = []
_acc = 0.0
for name, w in _TYPE_PRIOR:
    _acc += w
    _type_cumsum.append((_acc, name))

def pick_shot_type() -> str:
    u = random.random()
    for cum, name in _type_cumsum:
        if u <= cum:
            return name
    return _TYPE_PRIOR[-1][0]


def sample_release(sh_type: str) -> Vec2:
    prior = _PRIORS[sh_type]
    u = random.random()
    acc = 0.0
    for g in prior.gaussians:
        acc += g.weight
        if u <= acc:
            return g.sample()
    return prior.gaussians[-1].sample()


def sample_scalar(cdf: ScalarCDF) -> float:
    return cdf.sample()

def shot_prior(sh_type: str) -> ShotPrior:
    return _PRIORS[sh_type]
