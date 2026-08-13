"""
Player & coaching benches positioned outside the boards along the
south-side straight.

------
Benches are *off-ice* areas that the simulation engine may query for line
changes or penalty-served logic.  They are not collision objects for the puck
because boards separate them from the playing surface.

Key NHL layout
--------------
• Location .............. outside the boards on the same side as the
  penalty boxes (traditionally the timekeeper’s side).  i adopt
  the south side (–Y) for a right-handed coordinate system.

• Length per team ....... 24 ft (7.315 m) minimum – we model 25 ft for
  head-clearance between stanchions.

• Depth ................. 5 ft  (1.524 m) behind the boards

• Floor height .......... ice level (z = 0) – benches are sunken in most
  arenas but for simplicity we keep them level.

Geometry produced
----------------
Two rectangular 3-D boxes (Box3D) labelled “home_bench” and “away_bench”.

The centres of the benches are symmetric about centre ice to preserve
identical change distance for both teams.

Colour / textures are renderer decisions; no physics collisions are returned.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence, List, Dict

from puck_dynamics.geometry import Box3D  # type: ignore[attr-defined]

from ..base import ArenaFeature
from ..dimensions import NHLStandardDimensions, ft_to_m
from ..registry import register_feature

__all__ = ["Benches"]

LENGTH = ft_to_m(25)        # bench length
DEPTH  = ft_to_m(5)
WALL   = 0.05               # nominal wall thickness for rendering
EXTRUDE = 1.20              # seat-back height (visual only)


@dataclass(frozen=True, slots=True)
class Benches(ArenaFeature):

    dims: NHLStandardDimensions = NHLStandardDimensions()
    name: str = "benches"

    # Optional offset along X in case a specific arena wants non-symmetry
    x_offset: float = 0.0

    _cache: Sequence[object] | None = field(default=None, init=False, repr=False)
    _meta:   Dict[str, Box3D] | None = field(default=None, init=False, repr=False)

    def geometry(self) -> Sequence[object]:
        if self._cache is not None:
            return self._cache

        half_len_rink = self.dims.length / 2
        half_wid_rink = self.dims.width / 2
        r_corner      = self.dims.corner_radius

        # South straight board runs from x = −(half_len−r) … +(half_len−r)
        straight_x_min = -(half_len_rink - r_corner)
        straight_x_max = +(half_len_rink - r_corner)

        # Centre the two benches on either half of the south straight
        half_straight_len = (straight_x_max - straight_x_min) / 2

        bench_centre_offset = (half_straight_len - LENGTH) / 2

        # Away bench (west half)
        away_x0 = straight_x_min + bench_centre_offset + self.x_offset
        away_x1 = away_x0 + LENGTH

        # Home bench (east half)
        home_x1 = straight_x_max - bench_centre_offset + self.x_offset
        home_x0 = home_x1 - LENGTH

        y_inner = -half_wid_rink - WALL           # just outside dasher board
        y_outer = y_inner - DEPTH

        z0, z1 = 0.0, EXTRUDE

        away_box = Box3D.from_bounds(
            x_min=away_x0, x_max=away_x1,
            y_min=y_outer, y_max=y_inner,
            z_min=z0,     z_max=z1,
        )
        home_box = Box3D.from_bounds(
            x_min=home_x0, x_max=home_x1,
            y_min=y_outer, y_max=y_inner,
            z_min=z0,     z_max=z1,
        )

        object.__setattr__(self, "_cache", (away_box, home_box))
        object.__setattr__(self, "_meta", {"away_bench": away_box,
                                           "home_bench": home_box})
        return self._cache

    def benches(self) -> Dict[str, Box3D]:
        """
        Returns a dict with keys ``"home_bench"`` and ``"away_bench"`` mapping
        to their respective Box3D volumes.
        """
        if self._meta is None:
            self.geometry()               # populates _meta
        return self._meta                 # type: ignore[return-value]

    def collision_surfaces(self) -> Sequence[object]:
        """
        Benches are off-ice; no puck collision surfaces.
        """
        return []

register_feature("benches", Benches)

