from typing import Type, Mapping
from puck_dynamics.geometry import Box3D, Cylinder, Plane3D

_Surface = object
_Coeffs  = tuple[float, float, float]  # e, μ, spin-transfer (0…1)

_TABLE: Mapping[Type[_Surface], _Coeffs] = {
    Box3D:    (0.55, 0.30, 0.15),   # boards, glass share Box3D inner faces
    Cylinder: (0.60, 0.28, 0.12),   # rounded corners / posts
    Plane3D:  (0.40, 0.20, 0.05),   # ice
}

DEFAULT: _Coeffs = (0.5, 0.3, 0.1)

def props(surf: _Surface) -> _Coeffs:
    for cls, coeffs in _TABLE.items():
        if isinstance(surf, cls):
            return coeffs
    return DEFAULT
