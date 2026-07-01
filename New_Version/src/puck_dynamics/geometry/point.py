from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Iterable, Tuple

import numpy as np

ArrayLike = Iterable[float]


@dataclass(frozen=True)
class Point3D:
    """
    Immutable 3D point / vector.

    Parameters
    ----------
    x : float
        X coordinate.
    y : float
        Y coordinate.
    z : float
        Z coordinate.

    """
    x: float
    y: float
    z: float

    # Construction helpers -------------------------------------------------
    @classmethod
    def from_array(cls, arr: ArrayLike) -> "Point3D":
        """
        Create a Point3D from an iterable of three numbers.

        Parameters
        ----------
        arr : Iterable[float]
            Iterable containing exactly three numeric values (x, y, z).

        Returns
        -------
        Point3D
        """
        a = np.asarray(list(arr), dtype=float)
        if a.size != 3:
            raise ValueError("from_array requires an iterable of length 3")
        return cls(float(a[0]), float(a[1]), float(a[2]))

    @classmethod
    def zero(cls) -> "Point3D":
        """Return the origin (0, 0, 0)."""
        return cls(0.0, 0.0, 0.0)

    @classmethod
    def unit_x(cls) -> "Point3D":
        """Unit vector along +X."""
        return cls(1.0, 0.0, 0.0)

    @classmethod
    def unit_y(cls) -> "Point3D":
        """Unit vector along +Y."""
        return cls(0.0, 1.0, 0.0)

    @classmethod
    def unit_z(cls) -> "Point3D":
        """Unit vector along +Z."""
        return cls(0.0, 0.0, 1.0)

    # Representation / conversion -----------------------------------------
    def to_array(self) -> np.ndarray:
        """Return coordinates as a numpy array of shape (3,)."""
        return np.array([self.x, self.y, self.z], dtype=float)

    def as_tuple(self) -> Tuple[float, float, float]:
        """Return coordinates as a (x, y, z) tuple."""
        return (self.x, self.y, self.z)

    # Basic arithmetic ----------------------------------------------------
    def __add__(self, other: "Point3D") -> "Point3D":
        """Vector addition."""
        return Point3D(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Point3D") -> "Point3D":
        """Vector subtraction."""
        return Point3D(self.x - other.x, self.y - other.y, self.z - other.z)

    def __neg__(self) -> "Point3D":
        """Negation."""
        return Point3D(-self.x, -self.y, -self.z)

    def __mul__(self, scalar: float) -> "Point3D":
        """Scalar multiplication (vector * scalar)."""
        if not isinstance(scalar, (int, float)):
            return NotImplemented
        return Point3D(self.x * scalar, self.y * scalar, self.z * scalar)

    def __rmul__(self, scalar: float) -> "Point3D":
        """Scalar multiplication (scalar * vector)."""
        return self.__mul__(scalar)

    def __truediv__(self, scalar: float) -> "Point3D":
        """Scalar division."""
        if scalar == 0:
            raise ZeroDivisionError("Division by zero")
        return Point3D(self.x / scalar, self.y / scalar, self.z / scalar)

    # Vector operations ---------------------------------------------------
    def dot(self, other: "Point3D") -> float:
        """Dot product with another Point3D."""
        return float(self.x * other.x + self.y * other.y + self.z * other.z)

    def cross(self, other: "Point3D") -> "Point3D":
        """Cross product with another Point3D."""
        a = self.to_array()
        b = other.to_array()
        c = np.cross(a, b)
        return Point3D(float(c[0]), float(c[1]), float(c[2]))

    def norm(self) -> float:
        """Euclidean norm (length)."""
        return math.hypot(self.x, self.y, self.z)

    def norm_sq(self) -> float:
        """Squared Euclidean norm (length^2)."""
        return self.x * self.x + self.y * self.y + self.z * self.z

    def distance_to(self, other: "Point3D") -> float:
        """Euclidean distance to another point."""
        return (self - other).norm()

    def normalized(self) -> "Point3D":
        """Return a unit vector in the same direction.

        Raises
        ------
        ValueError
            If the vector is (near) zero length.
        """
        n = self.norm()
        if n == 0.0:
            raise ValueError("Cannot normalize zero-length vector")
        return self / n

    # Numerical comparisons ----------------------------------------------
    def is_close(self, other: "Point3D", tol: float = 1e-8) -> bool:
        """
        Component-wise comparison within tolerance.

        Parameters
        ----------
        other : Point3D
            Other point to compare.
        tol : float
            Absolute tolerance.

        Returns
        -------
        bool
        """
        return bool(np.allclose(self.to_array(), other.to_array(), atol=tol, rtol=0.0))

    # Utility -------------------------------------------------------------
    def project_onto(self, other: "Point3D") -> "Point3D":
        """
        Project this vector onto another vector (other may be non-unit).

        Returns
        -------
        Point3D
            The projection vector (parallel to other).
        """
        denom = other.norm_sq()
        if denom == 0.0:
            raise ValueError("Cannot project onto zero-length vector")
        scale = self.dot(other) / denom
        return other * scale

    def angle_with(self, other: "Point3D") -> float:
        """
        Angle (radians) between this vector and another.

        Returns
        -------
        float
        """
        n1 = self.norm()
        n2 = other.norm()
        if n1 == 0.0 or n2 == 0.0:
            raise ValueError("Angle undefined for zero-length vector")
        cos_theta = max(-1.0, min(1.0, self.dot(other) / (n1 * n2)))
        return math.acos(cos_theta)

    def lerp(self, other: "Point3D", t: float) -> "Point3D":
        """
        Linear interpolation between this point and `other`.

        Parameters
        ----------
        other : Point3D
        t : float
            Interpolation parameter in [0, 1].

        Returns
        -------
        Point3D
        """
        return Point3D(self.x + (other.x - self.x) * t,
                       self.y + (other.y - self.y) * t,
                       self.z + (other.z - self.z) * t)

    # String representation ------------------------------------------------
    def __repr__(self) -> str:
        return f"Point3D(x={self.x:.6g}, y={self.y:.6g}, z={self.z:.6g})"

