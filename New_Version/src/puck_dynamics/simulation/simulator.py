from __future__ import annotations
from typing import Callable, Iterable
import numpy as np

from puck_dynamics.geometry import Point3D as Vec
from puck_dynamics.arena import Rink
from puck_dynamics.physics import World, ShotFactory, Puck
from .trajectory import Trajectory
from .seating_grid import SeatingGrid
from .heatmap import Heatmap

ShotSampler = Callable[[Vec], Puck]

class Simulator:
    def __init__(self,
                 rink: Rink | None = None,
                 shots: int = 10_000,
                 sampler: ShotSampler | None = None,
                 record_path: bool = False):
        self.rink = rink or Rink()
        self.world = World(self.rink)
        self.num_shots = shots
        self.sampler = sampler or ShotFactory.wrist
        self.record_path = record_path
    def _spawn(self) -> Puck:
        origin = Vec(0, 0, 0.15)   # 15 cm above ice at centre by default
        return self.sampler(origin)

    def _run_single(self) -> Trajectory:
        puck = self._spawn()
        self.world.add(puck)

        traj = Trajectory(False, False, None)
        ticks = 0
        while ticks < 3_000:    # ~10 s @300 Hz max
            self.world.tick()
            if self.record_path:
                traj.record(puck.pos.copy())
            # out of play?
            if puck.pos.z < -0.1:          # fell “below ice” due to num error
                traj.out_of_play = True
                break
            if abs(puck.pos.x) > 40 or abs(puck.pos.y) > 25 or puck.pos.z > 25:
                # left arena envelope
                traj.landed = True
                traj.final_pos = puck.pos.copy()
                break
            # stationary on ice
            if puck.vel.norm() < 0.05 and puck.pos.z < 0.05:
                break
            ticks += 1
        return traj

    def run(self, grid: SeatingGrid,
            progress: bool = True) -> np.ndarray:
        hm = Heatmap(grid.shape)
        rng = range(self.num_shots)
        if progress:
            try:
                from tqdm import tqdm
                rng = tqdm(rng, desc="Simulating shots")
            except ImportError:
                pass

        for _ in rng:
            traj = self._run_single()
            if traj.landed and traj.final_pos is not None:
                idx = grid.index_of(traj.final_pos)
                if idx:
                    hm.increment(idx)

            self.world.pucks.clear()

        return hm.normalised()
