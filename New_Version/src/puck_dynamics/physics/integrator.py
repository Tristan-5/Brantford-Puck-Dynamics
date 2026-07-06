from puck_dynamics.geometry import Point3D as Vec
from .constants import DT, V_THRESH, SUBSTEP_MAX
from .forces import net, spin_decay
from .puck import Puck

def verlet_step(puck: Puck, dt: float = DT) -> None:
    a0 = net(puck) / puck.mass
    puck.state.pos += puck.vel * dt + a0 * (0.5 * dt * dt)
    # half-kick
    v_mid = puck.vel + a0 * (0.5 * dt)
    # recompute accel
    a1 = net(puck) / puck.mass
    puck.state.vel = v_mid + a1 * (0.5 * dt)
    spin_decay(puck, dt)

def step(puck: Puck, dt: float = DT) -> None:
    # split if fast
    sub = 1 + int(min(SUBSTEP_MAX-1, max(0, puck.vel.norm() // V_THRESH)))
    h = dt / sub
    for _ in range(sub):
        verlet_step(puck, h)
