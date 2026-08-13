from __future__ import annotations

import random
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from puck_dynamics.arena import Rink
from puck_dynamics.simulation.seating_grid import SeatingGrid
from puck_dynamics.simulation.simulator import Simulator
from puck_dynamics.simulation.shot_sampler import sample_shot


@dataclass(frozen=True)
class MetricTarget:
    name: str
    min_value: float
    max_value: float
    value: float

    @property
    def passed(self) -> bool:
        return self.min_value <= self.value <= self.max_value


def _q(arr: np.ndarray, q: float) -> float:
    return float(np.quantile(arr, q)) if arr.size else float("nan")


def _collect_out_of_play_depths(sim: Simulator, attempts: int) -> tuple[int, np.ndarray]:
    half_wid = sim.rink.dims.width / 2.0
    depths: list[float] = []
    out_of_play = 0
    for _ in range(attempts):
        traj = sim._run_single()
        sim.world.pucks.clear()
        if traj.landed and traj.out_of_play and traj.final_pos is not None:
            out_of_play += 1
            depths.append(abs(traj.final_pos.y) - half_wid)
    return out_of_play, np.array(depths, dtype=np.float64)


def _collect_shot_profile(samples: int, half_len: float) -> tuple[np.ndarray, np.ndarray]:
    speeds: list[float] = []
    abs_x: list[float] = []
    for _ in range(samples):
        shot = sample_shot()
        speeds.append(shot.speed)
        abs_x.append(abs(shot.origin.x))
    return np.array(speeds, dtype=np.float64), np.array(abs_x, dtype=np.float64)


def _collect_symmetry(sim: Simulator, grid: SeatingGrid, shots: int) -> tuple[float, float, float, float]:
    probs = sim.run_out_of_play_grid(grid, progress=False)
    probs = grid.debias_symmetry(probs, blend=0.65)

    dims = sim.rink.dims
    half_len = dims.length / 2.0
    half_wid = dims.width / 2.0
    x_min = -half_len - 40.0
    y_min = -half_wid - 40.0
    dx = dy = 0.25

    xs = x_min + (np.arange(probs.shape[0]) + 0.5) * dx
    ys = y_min + (np.arange(probs.shape[1]) + 0.5) * dy
    x, y = np.meshgrid(xs, ys, indexing="ij")

    q1 = float(probs[(x >= 0) & (y >= 0)].sum())
    q2 = float(probs[(x < 0) & (y >= 0)].sum())
    q3 = float(probs[(x < 0) & (y < 0)].sum())
    q4 = float(probs[(x >= 0) & (y < 0)].sum())

    side_delta = abs(float(probs[x < 0].sum()) - float(probs[x >= 0].sum()))
    diag_delta = abs((q1 + q3) - (q2 + q4))
    return q1, q2, q3, q4, side_delta, diag_delta


def main() -> None:
    random.seed(17)
    np.random.seed(17)

    sim = Simulator(rink=Rink(), shots=0, record_path=False)
    dims = sim.rink.dims
    half_len = dims.length / 2.0

    depth_trials = 8_000
    shot_samples = 20_000

    out_of_play_count, depths = _collect_out_of_play_depths(sim, depth_trials)
    speeds, abs_x = _collect_shot_profile(shot_samples, half_len)

    out_of_play_rate = out_of_play_count / depth_trials
    offensive_frac = float((abs_x > 0.58 * half_len).mean())
    neutral_frac = float((abs_x < 0.25 * half_len).mean())

    grid = SeatingGrid.outside_rink(sim.rink, dx=0.25, dy=0.25, margin=40.0)
    sim_for_grid = Simulator(rink=sim.rink, shots=14_000, record_path=False)
    q1, q2, q3, q4, side_delta, diag_delta = _collect_symmetry(sim_for_grid, grid, 14_000)

    metrics = [
        MetricTarget("OutOfPlayRate", 0.06, 0.16, out_of_play_rate),
        MetricTarget("DepthP10_m", 1.5, 6.5, _q(depths, 0.10)),
        MetricTarget("DepthP50_m", 4.0, 10.5, _q(depths, 0.50)),
        MetricTarget("DepthP90_m", 8.0, 18.0, _q(depths, 0.90)),
        MetricTarget("OffensiveReleaseFrac", 0.65, 0.82, offensive_frac),
        MetricTarget("NeutralReleaseFrac", 0.10, 0.28, neutral_frac),
        MetricTarget("SpeedP50_mps", 22.0, 30.5, _q(speeds, 0.50)),
        MetricTarget("SpeedP90_mps", 31.0, 38.0, _q(speeds, 0.90)),
        MetricTarget("SideSymmetryDelta", 0.0, 0.04, side_delta),
        MetricTarget("DiagSymmetryDelta", 0.0, 0.04, diag_delta),
    ]

    passed = sum(1 for m in metrics if m.passed)
    print(f"OHL calibration report: {passed}/{len(metrics)} metrics in range")
    print(f"samples: depth_trials={depth_trials} shot_samples={shot_samples}")
    print(f"quadrants: q1={q1:.4f} q2={q2:.4f} q3={q3:.4f} q4={q4:.4f}")
    print("metrics:")
    for m in metrics:
        status = "PASS" if m.passed else "FAIL"
        print(
            f"  {status:4s} {m.name:20s} value={m.value:.4f} "
            f"target=[{m.min_value:.4f}, {m.max_value:.4f}]"
        )

    if passed != len(metrics):
        print("suggestion: tune runout + zone weights and rerun this report before updating visuals")


if __name__ == "__main__":
    main()
