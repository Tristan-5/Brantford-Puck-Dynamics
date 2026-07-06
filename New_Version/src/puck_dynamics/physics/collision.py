from __future__ import annotations
from typing import List
from puck_dynamics.geometry import Point3D as Vec
from .puck import Puck
from .materials import props
from .bvh import Node as BVH
from .sweep import time_of_impact

class Collider:
    def __init__(self, surfaces: List[object]):
        self.bvh = BVH(surfaces)

    def handle(self, puck: Puck, dt: float) -> None:
        # 1. broad-phase candidates
        cand: List[object] = []
        self.bvh.query(puck.pos, puck.radius, cand)
        if not cand:
            return

        p_start = puck.pos
        p_end   = puck.pos + puck.vel * dt

        earliest_t = 1.1
        hit_surf   = None
        for s in cand:
            toi = time_of_impact(p_start, p_end, puck.radius, s)
            if toi is not None and toi < earliest_t:
                earliest_t, hit_surf = toi, s

        if hit_surf is None:
            return

        # Rewind to impact
        t_hit = earliest_t
        puck.state.pos = p_start + puck.vel * (t_hit * dt)

        # Impulse
        n = hit_surf.normal_at(puck.pos)
        e, mu, spin_xfer = props(hit_surf)

        v_n = n * puck.vel.dot(n)
        v_t = puck.vel - v_n

        # normal restitution (speed-dependent)
        e_eff = e * min(1.0, 10.0 / abs(v_n.norm()+1e-6))
        v_n_new = -e_eff * v_n

        # friction → reduce tangential, add spin
        v_t_new = v_t * (1.0 - mu)
        ω_new   = puck.ω + n.cross(v_t) * (spin_xfer / puck.radius)

        puck.state.vel = v_n_new + v_t_new
        puck.state.ω   = ω_new

        # advance remaining time slice recursively (rare)
        remain = (1.0 - t_hit) * dt
        if remain > 1e-5:
            self.handle(puck, remain)
