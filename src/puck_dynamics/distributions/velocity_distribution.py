from dataclasses import dataclass
import numpy as np

GOAL_X = 60.0
GOAL_Y = 12.95


@dataclass
class ShotType:
    name: str
    speed_mean: float
    speed_std: float
    elevation_mean_deg: float
    elevation_std_deg: float


WRIST = ShotType(
    "wrist",
    speed_mean=28,
    speed_std=4,
    elevation_mean_deg=10,
    elevation_std_deg=3,
)

SLAP = ShotType(
    "slap",
    speed_mean=42,
    speed_std=5,
    elevation_mean_deg=6,
    elevation_std_deg=2,
)


ZONE_SIGMA = {
    "slot": 5,
    "left_circle": 10,
    "right_circle": 10,
    "left_point": 15,
    "right_point": 15,
}


def sample_shot_type():
    return WRIST if np.random.rand() < 0.7 else SLAP


def sample_velocity(shot_x, shot_y, zone="slot"):

    shot_type = sample_shot_type()

    theta = np.arctan2(
        GOAL_Y - shot_y,
        GOAL_X - shot_x,
    )

    theta += np.radians(
        np.random.normal(
            0,
            ZONE_SIGMA.get(zone, 10),
        )
    )

    phi = np.radians(
        np.random.normal(
            shot_type.elevation_mean_deg,
            shot_type.elevation_std_deg,
        )
    )

    speed = max(
        np.random.normal(
            shot_type.speed_mean,
            shot_type.speed_std,
        ),
        5.0,
    )

    vx = speed * np.cos(phi) * np.cos(theta)
    vy = speed * np.cos(phi) * np.sin(theta)
    vz = speed * np.sin(phi)

    return {
        "shot_type": shot_type.name,
        "speed": speed,
        "vx": vx,
        "vy": vy,
        "vz": vz,
        "theta": theta,
        "phi": phi,
    }
