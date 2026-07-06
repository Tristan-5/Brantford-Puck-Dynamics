from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple
from puck_dynamics.geometry import Point3D as Vec

@dataclass(slots=True)
class Trajectory:
    landed: bool
    out_of_play: bool
    final_pos: Vec | None
    points: List[Vec] = field(default_factory=list)   # optional

    def record(self, p: Vec) -> None:
        self.points.append(p)
