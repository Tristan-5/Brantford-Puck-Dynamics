from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Type

from .base import ArenaFeature
from .rink import Rink
from .features.seating import Seating

__all__ = ["CivicCenter", "CivicCenterSeating"]


@dataclass(frozen=True, slots=True)
class CivicCenterSeating(Seating):
	"""
	Brantford Civic Centre-inspired lower bowl.

	This keeps the standard rink footprint while pulling the crowd a bit closer
	and lowering the overall bowl profile to match a more intimate junior arena.
	"""

	rows: int = 18
	row_depth: float = 0.82
	row_rise: float = 0.32
	clear_ring: float = 2.75


@dataclass
class CivicCenter(Rink):
	"""
	Rink preset with a tighter, lower seating bowl for Brantford-style exports.
	"""

	feature_overrides: Dict[str, Type[ArenaFeature]] = field(
		default_factory=lambda: {"seating": CivicCenterSeating}
	)

