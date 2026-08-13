from __future__ import annotations
from typing import Callable, Iterable
from dataclasses import dataclass
import numpy as np

from puck_dynamics.geometry import Point3D as Vec
from puck_dynamics.arena import Rink
from puck_dynamics.arena.features.netting import Netting
from puck_dynamics.physics.constants import G
from puck_dynamics.physics import World, ShotFactory, Puck
from .trajectory import Trajectory
from .seating_grid import SeatingGrid
from .heatmap import Heatmap
from .shot_sampler import sample_shot, ShotSamplingConfig

ShotSampler = Callable[[Vec], Puck]


@dataclass(frozen=True, slots=True)
class LandingModelConfig:
    decel_min: float = 12.5
    decel_max: float = 20.5
    retention_alpha: float = 2.5
    retention_beta: float = 3.0
    crowd_depth_min: float = 3.5
    crowd_depth_mode: float = 8.0
    crowd_depth_max: float = 19.0
    max_flight_time_s: float = 0.45
    min_total_distance_m: float = 0.20


DEFAULT_LANDING_CONFIG = LandingModelConfig()

class Simulator:
    def __init__(self,
                 rink: Rink | None = None,
                 shots: int = 10_000,
                 record_path: bool = False,
                 shot_config: ShotSamplingConfig | None = None,
                 landing_config: LandingModelConfig | None = None):
        self.rink = rink or Rink()
        self.world = World(self.rink)
        self.num_shots = shots
        self.record_path = record_path
        self.shot_config = shot_config
        self.landing_config = landing_config or DEFAULT_LANDING_CONFIG
        self._pending_mirror_spec = None

    def _spawn(self) -> Puck:
        if self._pending_mirror_spec is not None:
            spec = self._pending_mirror_spec
            self._pending_mirror_spec = None
        else:
            spec = sample_shot(config=self.shot_config)
            self._pending_mirror_spec = self._mirror_shot_spec(spec)
        return ShotFactory.from_spec(spec)

    def _mirror_shot_spec(self, spec):
        """Create a 180-degree mirrored companion shot to reduce sampling bias."""
        mirrored_origin = Vec(-spec.origin.x, -spec.origin.y, spec.origin.z)
        mirrored_azim = ((spec.azim + 180.0) % 360.0) - 180.0
        return type(spec)(
            type=spec.type,
            origin=mirrored_origin,
            speed=spec.speed,
            elev=spec.elev,
            azim=mirrored_azim,
            spin=spec.spin,
        )

    def _project_side_landing(self,
                              puck: Puck,
                              side_sign: float,
                              half_len: float,
                              half_wid: float) -> Vec:
        x_cross = min(max(puck.pos.x, -half_len), half_len)
        y_cross = side_sign * half_wid

        vx, vy, vz = puck.vel.x, puck.vel.y, puck.vel.z
        vxy = Vec(vx, vy, 0.0)
        speed_xy = vxy.norm()

        # Airborne drift until the puck returns near ice level.
        z0 = max(0.0, puck.pos.z)
        disc = vz * vz + 2.0 * G * z0
        t_flight = (vz + np.sqrt(max(0.0, disc))) / G if G > 0 else 0.0
        cfg = self.landing_config
        t_flight = min(max(0.0, t_flight), cfg.max_flight_time_s)
        airborne = speed_xy * t_flight

        # Ground runout after crossing side boards (OHL-like bowl calibration).
        # Use stochastic friction + crowd-depth truncation to avoid any single
        # hard global cutoff band in the rendered density.
        decel = float(np.random.uniform(cfg.decel_min, cfg.decel_max))
        runout_phys = (speed_xy * speed_xy) / (2.0 * decel) if decel > 0 else 0.0
        # Secondary contacts/deflections reduce effective runout.
        retention = float(np.random.beta(cfg.retention_alpha, cfg.retention_beta))
        # Effective accessible depth outside boards varies by section.
        crowd_depth = float(
            np.random.triangular(
                cfg.crowd_depth_min,
                cfg.crowd_depth_mode,
                cfg.crowd_depth_max,
            )
        )
        runout = min(runout_phys * retention, crowd_depth)
        total = max(cfg.min_total_distance_m, airborne + runout)

        if speed_xy > 1e-6:
            direction = vxy.normalized()
            if side_sign * direction.y <= 0.0:
                direction = Vec(0.0, side_sign, 0.0)
        else:
            direction = Vec(0.0, side_sign, 0.0)

        landed = Vec(
            x_cross + direction.x * total,
            y_cross + direction.y * total,
            max(0.0, puck.pos.z + vz * t_flight - 0.5 * G * t_flight * t_flight),
        )
        return landed

    def _out_of_play_point(self, puck: Puck) -> tuple[Vec | None, str | None]:
        dims = self.rink.dims
        half_len = dims.length / 2.0
        half_wid = dims.width / 2.0
        side_straight_x = half_len - dims.corner_radius

        if puck.pos.z < -0.1:
            return (puck.pos.copy(), 'below')

        # Only side straightaways are valid out-of-play exits. Corner and end
        # departures are treated as netting-blocked.
        if abs(puck.pos.y) > half_wid:
            side_sign = 1.0 if puck.pos.y > 0 else -1.0
            x = min(max(puck.pos.x, -half_len), half_len)
            reason = 'boundary' if abs(x) <= side_straight_x else 'netting'
            projected = self._project_side_landing(
                puck,
                side_sign=side_sign,
                half_len=half_len,
                half_wid=half_wid,
            )
            return (projected, reason)

        if abs(puck.pos.x) > half_len:
            x = half_len if puck.pos.x > 0 else -half_len
            y = min(max(puck.pos.y, -half_wid), half_wid)
            x += 0.20 if puck.pos.x > 0 else -0.20
            return (Vec(x, y, puck.pos.z), 'netting')

        return (None, None)

    def _run_single(self) -> Trajectory:
        puck = self._spawn()
        self.world.add(puck)

        traj = Trajectory(False, False, None)
        ticks = 0
        while ticks < 3_000:    # ~10 s @300 Hz max
            self.world.tick()
            if self.record_path:
                traj.record(puck.pos.copy())

            out_point, reason = self._out_of_play_point(puck)
            if out_point is not None:
                traj.landed = True
                # Only side-boundary exits are counted as out-of-play.
                traj.out_of_play = (reason == 'boundary')
                traj.final_pos = out_point
                break

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
            # Only count pucks that landed out-of-play (exclude netting-dead pucks)
            if traj.landed and traj.final_pos is not None and traj.out_of_play:
                idx = grid.index_of(traj.final_pos)
                if idx:
                    hm.increment(idx)

            self.world.pucks.clear()

        return hm.normalised()

    def run_out_of_play_grid(self, grid: SeatingGrid,
                             progress: bool = True) -> np.ndarray:
        """Numerically estimate where out-of-play pucks are most likely to land.

        The grid is expressed in the rink's centered coordinate system so that
        the same XY positions can be inspected directly in the simulation.
        """
        return self.run(grid, progress=progress)
