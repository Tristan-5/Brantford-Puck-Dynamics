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
import math

from puck_dynamics.geometry import (               # type: ignore[attr-defined]
    Plane3D,
    Point3D,
    Polyline2D,
    Arc,
    Circle,
    Box3D,
)

from ..base import ArenaFeature
from ..dimensions import NHLStandardDimensions, ft_to_m
from ..colors import ICE_BLUE
from ..registry import register_feature

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

        # Collision / physics plane (the actual playing surface footprint)
        geom.append(
            Plane3D.rectangle_xy(
                width=self.dims.length,
                height=self.dims.width,
                center=(0.0, 0.0, 0.0),
            )
        )

        # Build the rounded rink outline using straight sections plus
        # discretized quarter-circle arcs so the ice shape fills correctly.
        outline_pts: List[Point3D] = []

        # East straight segment
        outline_pts.append(Point3D(half_len, -half_wid + r, 0))
        outline_pts.append(Point3D(half_len, +half_wid - r, 0))

        circle_ne = Circle(
            center=Point3D(half_len - r, half_wid - r, 0.0),
            normal=Point3D(0.0, 0.0, 1.0),
            radius=r,
        )
        arc_ne = Arc(
            circle=circle_ne,
            start_angle=0.0,
            end_angle=math.radians(90.0),
            clockwise=False,
        )
        outline_pts.extend(arc_ne.discretize(32)[1:])

        # North straight segment
        outline_pts.append(Point3D(+(half_len - r), +half_wid, 0))
        outline_pts.append(Point3D(-(half_len - r), +half_wid, 0))

        circle_nw = Circle(
            center=Point3D(-half_len + r, half_wid - r, 0.0),
            normal=Point3D(0.0, 0.0, 1.0),
            radius=r,
        )
        arc_nw = Arc(
            circle=circle_nw,
            start_angle=math.radians(90.0),
            end_angle=math.radians(180.0),
            clockwise=False,
        )
        outline_pts.extend(arc_nw.discretize(32)[1:])

        # West straight segment
        outline_pts.append(Point3D(-half_len, +(half_wid - r), 0))
        outline_pts.append(Point3D(-half_len, -(half_wid - r), 0))

        circle_sw = Circle(
            center=Point3D(-half_len + r, -half_wid + r, 0.0),
            normal=Point3D(0.0, 0.0, 1.0),
            radius=r,
        )
        arc_sw = Arc(
            circle=circle_sw,
            start_angle=math.radians(180.0),
            end_angle=math.radians(270.0),
            clockwise=False,
        )
        outline_pts.extend(arc_sw.discretize(32)[1:])

        # South straight segment
        outline_pts.append(Point3D(-(half_len - r), -half_wid, 0))
        outline_pts.append(Point3D(+(half_len - r), -half_wid, 0))

        circle_se = Circle(
            center=Point3D(half_len - r, -half_wid + r, 0.0),
            normal=Point3D(0.0, 0.0, 1.0),
            radius=r,
        )
        arc_se = Arc(
            circle=circle_se,
            start_angle=math.radians(270.0),
            end_angle=math.radians(360.0),
            clockwise=False,
        )
        outline_pts.extend(arc_se.discretize(32)[1:])

        outline_pts.append(outline_pts[0])
        outline = Polyline2D(outline_pts)
        geom.append(outline)

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
