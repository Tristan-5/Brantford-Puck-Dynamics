"""
Flat ice surface including the canonical 28-ft rounded corners.

The geometry is intentionally minimalist:

1.  A single :class:`puck_dynamics.geometry.Plane3D` whose XY footprint equals
    the official rink outline (rectangle + four quarter-circles).

2.  A closed :class:`puck_dynamics.geometry.Polyline2D` that traces the same
    outline so renderers can draw the rink border with anti-aliased curves.

3.  Optional hash-marks (short perpendicular dashes that mark face-off
    locations).  These are represented as thin ``Box3D`` paint extrusions;
    enable them with ``include_hashmarks=True``.  They donot participate
    in puck collision.

Nothing in this file computes forces or trajectories.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence

from puck_dynamics.geometry import (               # type: ignore[attr-defined]
    Plane3D,
    Point3D,
    Polyline2D,
    Arc2D,
    Box3D,
)

from ..base import ArenaFeature
from ..dimensions import NHLStandardDimensions, ft_to_m
from ..colors import ICE_BLUE
from .. import register_feature

__all__ = ["RinkSurface"]


HASH_LENGTH = ft_to_m(2)         # 2 ft long
HASH_WIDTH = ft_to_m(2 / 12)     # 2-inch paint stripe
HASH_OFFSET = ft_to_m(5)         # distance from end zone face-off spots
PAINT_Z = 0.002                  # 2-mm extrusion



@dataclass(frozen=True, slots=True)
class RinkSurface(ArenaFeature):


    dims: NHLStandardDimensions = NHLStandardDimensions()
    include_hashmarks: bool = True
    name: str = "rink_surface"

    _cache: Sequence[object] | None = field(default=None, init=False, repr=False)


    def geometry(self) -> Sequence[object]:
        if self._cache is not None:
            return self._cache

        geom: List[object] = []

        # We model the footprint analytically via Polyline/Arcs for rendering
        # but the collision plane is a single rectangle; the rounded corners
        # do not affect 2-D collision (they lie outside the playing surface).
        half_len = self.dims.length / 2.0
        half_wid = self.dims.width / 2.0
        r = self.dims.corner_radius

        # Collision / physics plane (full rectangle)
        geom.append(
            Plane3D.rectangle_xy(
                width=self.dims.width + 2 * r,
                height=self.dims.length,
                center=(0.0, 0.0, 0.0),
            )
        )

        # Build polyline  (start at east straight–corner junction, CCW)
        p = []
        # East straight (northwards)
        p.append(Point3D(half_len, -half_wid + r, 0))
        p.append(Point3D(half_len, +half_wid - r, 0))
        # NE arc  (quarter-circle)
        arc_ne = Arc2D(
            center=(half_len - r, half_wid - r),
            radius=r,
            start_angle=0.0,
            end_angle=+90.0,
            ccw=True,
        )
        # North straight
        p.append(Point3D(+(half_len - r), +half_wid, 0))
        p.append(Point3D(-(half_len - r), +half_wid, 0))
        # NW arc
        arc_nw = Arc2D(
            center=(-half_len + r, half_wid - r),
            radius=r,
            start_angle=+90.0,
            end_angle=+180.0,
            ccw=True,
        )
        # West straight
        p.append(Point3D(-half_len, +(half_wid - r), 0))
        p.append(Point3D(-half_len, -(half_wid - r), 0))
        # SW arc
        arc_sw = Arc2D(
            center=(-half_len + r, -half_wid + r),
            radius=r,
            start_angle=+180.0,
            end_angle=+270.0,
            ccw=True,
        )
        # South straight
        p.append(Point3D(-(half_len - r), -half_wid, 0))
        p.append(Point3D(+(half_len - r), -half_wid, 0))
        # SE arc
        arc_se = Arc2D(
            center=(half_len - r, -half_wid + r),
            radius=r,
            start_angle=+270.0,
            end_angle=+360.0,
            ccw=True,
        )

        outline = Polyline2D(list(p) + [p[0]], closed=True)
        geom.extend([outline, arc_ne, arc_nw, arc_sw, arc_se])

        if self.include_hashmarks:
            geom.extend(self._make_hashmarks())

        object.__setattr__(self, "_cache", tuple(geom))
        return self._cache

    def _make_hashmarks(self) -> List[Box3D]:
        """
        Returns eight painted hash-marks (four in each end zone).
        Reference: centre of end-zone face-off spot is 20 ft from goal line
        and 22 ft from rink centreline. Hash-marks are ±5 ft from that spot.
        """
        geom: List[Box3D] = []
        half_len = self.dims.length / 2.0
        half_wid = self.dims.width / 2.0

        # X-positions of the two end-zone face-off spots
        goal_line_x = half_len - self.dims.goal_line_distance
        spot_offset = ft_to_m(20)          # centre of face-off spot from goal line
        spot_x_east = goal_line_x - spot_offset
        spot_x_west = -spot_x_east

        # Hash-marks are ± HASH_OFFSET in Y from the face-off spot
        y_offsets = [+(HASH_OFFSET / 2), -(HASH_OFFSET / 2)]

        z0, z1 = 0.0, PAINT_Z
        for spot_x in (spot_x_east, spot_x_west):
            for side in (+1, -1):  # +1 north half, −1 south half
                y_centre = side * (ft_to_m(22) / 2)
                for dy in y_offsets:
                    y0 = y_centre + dy - HASH_LENGTH / 2
                    y1 = y_centre + dy + HASH_LENGTH / 2
                    geom.append(
                        Box3D.from_bounds(
                            x_min=spot_x - HASH_WIDTH / 2,
                            x_max=spot_x + HASH_WIDTH / 2,
                            y_min=y0,
                            y_max=y1,
                            z_min=z0,
                            z_max=z1,
                        )
                    )
        return geom


    def collision_surfaces(self) -> Sequence[object]:
        """
        Only the *plane* represents a physical surface; paint and outline are
        ignored for collision.
        """
        return (self.geometry()[0],)  # first element is the Plane3D

register_feature("rink_surface", RinkSurface)
