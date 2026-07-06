from puck_dynamics.geometry import Point3D as Vec
from .constants import G, RHO_AIR, PI, C_D, C_L, SPIN_DECAY
from .puck import Puck

DISC_AREA = PI * (0.0381**2)

def gravity(puck: Puck) -> Vec:
    return Vec(0, 0, -puck.mass * G)

def drag(puck: Puck) -> Vec:
    v = puck.vel
    speed = v.norm()
    if speed == 0:
        return Vec.zero()
    f_mag = 0.5 * RHO_AIR * C_D * DISC_AREA * speed**2
    return v.normalized() * -f_mag

def magnus(puck: Puck) -> Vec:
    # F_lift = C_L * ρ * A * (ω × v)
    ω = puck.ω
    v = puck.vel
    lift_dir = ω.cross(v)
    if lift_dir.is_zero():
        return Vec.zero()
    f_mag = 0.5 * RHO_AIR * C_L * DISC_AREA * v.norm() * ω.norm()
    return lift_dir.normalized() * f_mag

def net(puck: Puck) -> Vec:
    return gravity(puck) + drag(puck) + magnus(puck)

def spin_decay(puck: Puck, dt: float) -> None:
    puck.state.ω *= (1.0 - SPIN_DECAY * dt)
