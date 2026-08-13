from __future__ import annotations

import math
from dataclasses import dataclass

from puck_dynamics.geometry import Point3D, Transform  # type: ignore[attr-defined]


@dataclass(frozen=True, slots=True)
class RinkCoordinateSystem:
  
    @classmethod
    def centered_origin(cls) -> "RinkCoordinateSystem":
        """
        Standard identity mapping—rink coordinates equal world coordinates.
        """
        return cls(Transform.identity())

    @classmethod
    def broadcast_view(cls) -> "RinkCoordinateSystem":
        rot_z = Transform.rotation_z(-math.pi / 2.0)  # 90° clockwise
        translate = Transform.translation(0, 0, 15.0)  # 15 m camera
        return cls(translate @ rot_z)

    def to_world(self, point: Point3D) -> Point3D:
        return self.rink_to_world * point

    def from_world(self, point: Point3D) -> Point3D:
        return self.rink_to_world.inverse() * point

