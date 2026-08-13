"""
Spectator*seating bowl–a coarse‐grained geometric shell that surrounds
the rink, useful for camera collision, crowd-occlusion calculations, and
approximate sound-propagation models.  It is not meant to represent every
individual seat; that would belong in the rendering pipeline.

Design assumptions
----------------
1. NHL arenas vary, but lower-bowl seating typically begins 8 ft above the
   ice (dasher + shielding glass) and rises at ~12 °–15 °.
2. The lower bowl ends ~40 ft above the ice after 24 rows.  We extend
   slightly beyond that so the shell over-covers corner luxury boxes.
3. I model the bowl as concentric rectangular rings with rounded
   corners (matching the rink footprint) extruded upward.
4. Only one solid ``MeshShell`` (or fallback to a Box3D stack) is created
   per side; collision with the puck is disabled.

Parameters exposed
--------------
• `rows` ............... integer, default 24  
• `row_depth` .......... 0.80 m – nose-to-nose distance  
• `row_rise` ........... 0.35 m – elevation gain per row  
• `clear_ring` ......... 4.00 m – horizontal gap between boards glass and
                         first row (walkway / TV cameras)

Geometry returned
----------------
A list of simple Box3D volumes (one per side + four corner wedges) or a
single triangulated MeshShell if an advanced geometry back-end is present.
For portability we stick with boxes + corner cylinders here.


"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import atan, tan, radians
from typing import List, Sequence

from puck_dynamics.geometry import Arc, Box3D, Circle, Cylinder, Point3D  # type: ignore[attr-defined]

from ..base import ArenaFeature
from ..dimensions import NHLStandardDimensions, ft_to_m
from ..registry import register_feature

__all__ = ["Seating"]

ROWS        = 24
ROW_DEPTH   = 0.80            # m
ROW_RISE    = 0.35            # m
CLEAR_RING  = ft_to_m(4 * 2)  # 8-ft walkway between glass and first row

# Glass height used as vertical origin of first row
GLASS_H     = ft_to_m(8)      # 8-ft shielding glass

@dataclass(frozen=True, slots=True)
class Seating(ArenaFeature):
    """
    Coarse seating bowl (lower bowl) around the rink.
    """

    dims: NHLStandardDimensions = NHLStandardDimensions()

    rows: int   = ROWS
    row_depth: float = ROW_DEPTH
    row_rise: float  = ROW_RISE
    clear_ring: float = CLEAR_RING

    name: str = "seating"

    _cache: Sequence[object] | None = field(default=None, init=False, repr=False)

    def geometry(self) -> Sequence[object]:
        if self._cache is not None:
            return self._cache

        half_len = self.dims.length / 2
        half_wid = self.dims.width / 2
        corner_r = self.dims.corner_radius

        inner_x = half_len - corner_r + self.clear_ring
        inner_y = half_wid + self.clear_ring

        # Overall depth and height
        total_depth = self.rows * self.row_depth
        total_height = GLASS_H + self.rows * self.row_rise

        outer_x = inner_x + total_depth
        outer_y = inner_y + total_depth

        z0 = GLASS_H               # seating starts above glass
        z1 = total_height

        geom: List[object] = []

        # Four straight side seating blocks (south, north, east, west)
        geom.append(Box3D.from_bounds(
            x_min=-(outer_x),
            x_max=+(outer_x),
            y_min=+(inner_y),
            y_max=+(outer_y),
            z_min=z0, z_max=z1,
        ))
        geom.append(Box3D.from_bounds(
            x_min=-(outer_x),
            x_max=+(outer_x),
            y_min=-(outer_y),
            y_max=-(inner_y),
            z_min=z0, z_max=z1,
        ))
        geom.append(Box3D.from_bounds(
            x_min=+(inner_x),
            x_max=+(outer_x),
            y_min=-(inner_y),
            y_max=+(inner_y),
            z_min=z0, z_max=z1,
        ))
        geom.append(Box3D.from_bounds(
            x_min=-(outer_x),
            x_max=-(inner_x),
            y_min=-(inner_y),
            y_max=+(inner_y),
            z_min=z0, z_max=z1,
        ))

        # Four cylindrical corner wedges (quarter cylinders)
        # Represented as full cylinders (wasteful but simple)
        corner_inner_r = corner_r + self.clear_ring
        corner_outer_r = corner_inner_r + total_depth
        corner_centres = [
            ((+half_len - corner_r, +half_wid - corner_r), 0.0, radians(90.0)),
            ((+half_len - corner_r, -half_wid + corner_r), radians(270.0), radians(360.0)),
            ((-half_len + corner_r, -half_wid + corner_r), radians(180.0), radians(270.0)),
            ((-half_len + corner_r, +half_wid - corner_r), radians(90.0), radians(180.0)),
        ]
        for (cx, cy), start_ang, end_ang in corner_centres:
            geom.append(Cylinder(
                base_center=Point3D(cx, cy, z0),
                axis=Point3D(0, 0, 1),
                radius=corner_outer_r,
                height=z1 - z0,
            ))
            geom.append(Arc(
                circle=Circle(
                    center=Point3D(cx, cy, 0.0),
                    normal=Point3D(0.0, 0.0, 1.0),
                    radius=corner_outer_r,
                ),
                start_angle=start_ang,
                end_angle=end_ang,
                clockwise=False,
            ))

        object.__setattr__(self, "_cache", tuple(geom))
        return self._cache

    def collision_surfaces(self) -> Sequence[object]:
        """
        The seating shell is not in bounds, but we still expose it so the
        engine can detect when a puck or player collides with it.
        """
        return self.geometry()     # <-- provide full shell as colliders


register_feature("seating", Seating)
