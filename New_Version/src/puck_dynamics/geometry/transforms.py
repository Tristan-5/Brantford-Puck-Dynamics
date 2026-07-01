from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Tuple

import numpy as np

from puck_dynamics.geometry.point import Point3D


@dataclass(frozen=True)
class Transform:

    matrix: np.ndarray

    def __post_init__(self) -> None:
        mat = np.asarray(self.matrix, dtype=float)
        if mat.shape != (4, 4):
            raise ValueError("matrix must be 4x4")
        object.__setattr__(self, "matrix", mat.copy())

    # Construction helpers ------------------------------------------------
    @classmethod
    def identity(cls) -> "Transform":
        """Return identity transform."""
        return cls(np.eye(4, dtype=float))

    @classmethod
    def translation(cls, tx: float, ty: float, tz: float) -> "Transform":
        m = np.eye(4, dtype=float)
        m[0:3, 3] = [tx, ty, tz]
        return cls(m)

    @classmethod
    def scale(cls, sx: float, sy: float, sz: float) -> "Transform":
        m = np.diag([sx, sy, sz, 1.0])
        return cls(m)

    @classmethod
    def rotation_axis_angle(cls, axis: Tuple[float, float, float], angle_rad: float) -> "Transform":

        ax = np.asarray(axis, dtype=float)
        nrm = np.linalg.norm(ax)
        if nrm == 0.0:
            raise ValueError("rotation axis cannot be zero vector")
        u = ax / nrm
        ux, uy, uz = u
        c = math.cos(angle_rad)
        s = math.sin(angle_rad)
        R = np.array([
            [c + ux*ux*(1-c),     ux*uy*(1-c) - uz*s, ux*uz*(1-c) + uy*s],
            [uy*ux*(1-c) + uz*s,  c + uy*uy*(1-c),    uy*uz*(1-c) - ux*s],
            [uz*ux*(1-c) - uy*s,  uz*uy*(1-c) + ux*s, c + uz*uz*(1-c)]
        ], dtype=float)
        M = np.eye(4, dtype=float)
        M[0:3, 0:3] = R
        return cls(M)

    @classmethod
    def rotation_euler_zyx(cls, z_rad: float, y_rad: float, x_rad: float) -> "Transform":

        Rz = cls.rotation_axis_angle((0.0, 0.0, 1.0), z_rad).matrix[0:3, 0:3]
        Ry = cls.rotation_axis_angle((0.0, 1.0, 0.0), y_rad).matrix[0:3, 0:3]
        Rx = cls.rotation_axis_angle((1.0, 0.0, 0.0), x_rad).matrix[0:3, 0:3]
        R = Rz @ Ry @ Rx
        M = np.eye(4, dtype=float)
        M[0:3, 0:3] = R
        return cls(M)

    # Operations -------------------------------------------------------
    def apply(self, p: Point3D) -> Point3D:
        """Apply transform to a Point3D and return a new Point3D."""
        v = np.array([p.x, p.y, p.z, 1.0], dtype=float)
        r = self.matrix @ v
        return Point3D(float(r[0]), float(r[1]), float(r[2]))

    def inverse(self) -> "Transform":
        """Return inverse transform."""
        inv = np.linalg.inv(self.matrix)
        return Transform(inv)

    def compose(self, other: "Transform") -> "Transform":

        return Transform(self.matrix @ other.matrix)

    # Convenience: transform a vector (no translation)
    def apply_vector(self, v: Tuple[float, float, float]) -> Tuple[float, float, float]:
        arr = np.array([v[0], v[1], v[2], 0.0], dtype=float)
        r = self.matrix @ arr
        return float(r[0]), float(r[1]), float(r[2])

