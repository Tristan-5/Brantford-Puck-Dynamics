import math

# core
G            = 9.80665          # m/s²
RHO_AIR      = 1.225            # kg/m³ @15 °C, sea level
PI           = math.pi

# integration
DT           = 1.0 / 300.0      # base step (300 Hz)
SUBSTEP_MAX  = 4                # ≤ this many sub-steps if |v| large
V_THRESH     = 45.0             # m/s; above → split step

# aerodynamic / Magnus
C_D          = 0.9              # drag coeff (flat disk)
C_L          = 0.22             # lift coeff vs spin
SPIN_DECAY   = 0.15             # fractional ω loss per second

# CCD safety
SWEEP_EPS    = 1e-6
