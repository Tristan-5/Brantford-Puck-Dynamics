from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path
from types import MappingProxyType
from typing import Dict, List, Sequence, Type

from .base import ArenaFeature
from .dimensions import NHLStandardDimensions


_FEATURE_PACKAGE = "puck_dynamics.arena.features"


def _discover_feature_classes() -> Dict[str, Type[ArenaFeature]]:
    classes: Dict[str, Type[ArenaFeature]] = {}

    pkg_path = Path(import_module(_FEATURE_PACKAGE).__file__).parent

    for py in pkg_path.glob("*.py"):
        if py.stem.startswith("_"):
            continue

        mod = import_module(f"{_FEATURE_PACKAGE}.{py.stem}")

        for attr in getattr(mod, "__all__", []):
            cls = getattr(mod, attr, None)

            if (
                isinstance(cls, type)
                and issubclass(cls, ArenaFeature)
            ):
                classes[attr] = cls

    return classes


_ALL_FEATURES: MappingProxyType[str, Type[ArenaFeature]] = MappingProxyType(
    _discover_feature_classes()
)

@dataclass
class Rink:
    """
    High-level composite representing an NHL rink with standard features.
    """

    dims: NHLStandardDimensions = NHLStandardDimensions()

    # Toggles for individual features
    enabled_features: Dict[str, bool] = field(
        default_factory=lambda: {
            name: True for name in _ALL_FEATURES
        }
    )

    # Optional class overrides {feature_name: CustomSubClass}
    feature_overrides: Dict[str, Type[ArenaFeature]] = field(
        default_factory=dict
    )

    # Caches
    _instances: Dict[str, ArenaFeature] = field(
        init=False,
        default_factory=dict,
    )

    _geom_cache: Sequence[object] | None = field(
        init=False,
        default=None,
    )

    _collision_cache: Sequence[object] | None = field(
        init=False,
        default=None,
    )

    def __getattr__(self, item: str):
        """
        Dot-access child: `rink.boards`, `rink.goal`, etc.
        """
        if item in _ALL_FEATURES:
            return self._get_feature(item)

        raise AttributeError(item)

    def _get_feature(self, name: str) -> ArenaFeature:
        if not self.enabled_features.get(name, True):
            raise AttributeError(f"Feature '{name}' is disabled")

        if name not in self._instances:
            cls = self.feature_overrides.get(name, _ALL_FEATURES[name])
            self._instances[name] = cls(dims=self.dims)  # type: ignore[arg-type]

        return self._instances[name]

    def geometry(self) -> Sequence[object]:
        if self._geom_cache is None:
            geo: List[object] = []

            for name in _ALL_FEATURES:
                if self.enabled_features.get(name, True):
                    geo.extend(self._get_feature(name).geometry())

            self._geom_cache = tuple(geo)

        return self._geom_cache

    def collision_surfaces(self) -> Sequence[object]:
        if self._collision_cache is None:
            coll: List[object] = []

            for name in _ALL_FEATURES:
                if self.enabled_features.get(name, True):
                    coll.extend(
                        self._get_feature(name).collision_surfaces()
                    )

            self._collision_cache = tuple(coll)

        return self._collision_cache


    def features(self):
        """
        Iterate instantiated feature objects.
        """
        for name in _ALL_FEATURES:
            if self.enabled_features.get(name, True):
                yield self._get_feature(name)

    def __repr__(self) -> str:
        active = ", ".join(
            n for n, on in self.enabled_features.items() if on
        )

        return f"<Rink features=[{active}] dims={self.dims}>"
