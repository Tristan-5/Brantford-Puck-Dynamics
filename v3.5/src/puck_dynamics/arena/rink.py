from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path
from typing import Dict, List, Sequence, Type

from .base import ArenaFeature
from .dimensions import NHLStandardDimensions
from .registry import get_registered_features


_FEATURE_PACKAGE = "puck_dynamics.arena.features"


def _discover_feature_classes() -> Dict[str, Type[ArenaFeature]]:
    try:
        pkg = import_module(_FEATURE_PACKAGE)
        pkg_path = Path(pkg.__file__).parent if pkg.__file__ is not None else None
    except Exception:
        pkg_path = None

    if pkg_path is not None:
        for py in pkg_path.glob("*.py"):
            if py.stem.startswith("_"):
                continue

            try:
                import_module(f"{_FEATURE_PACKAGE}.{py.stem}")
            except Exception:
                continue

    return get_registered_features()


_ALL_FEATURES: Dict[str, Type[ArenaFeature]] = {}

@dataclass
class Rink:
    """
    High-level composite representing an NHL rink with standard features.
    """

    dims: NHLStandardDimensions = NHLStandardDimensions()

    # Toggles for individual features
    enabled_features: Dict[str, bool] = field(default_factory=dict)

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

    def _refresh_feature_catalog(self) -> None:
        discovered = _discover_feature_classes()
        for name, cls in discovered.items():
            if name not in _ALL_FEATURES:
                _ALL_FEATURES[name] = cls
        for name in list(self.enabled_features.keys()):
            if name not in discovered:
                self.enabled_features.pop(name, None)
        if not self.enabled_features:
            for name in discovered:
                self.enabled_features[name] = True

    def __getattr__(self, item: str):
        """
        Dot-access child: `rink.boards`, `rink.goal`, etc.
        """
        self._refresh_feature_catalog()
        if item in _ALL_FEATURES:
            return self._get_feature(item)

        raise AttributeError(item)

    def _get_feature(self, name: str) -> ArenaFeature:
        self._refresh_feature_catalog()
        if not self.enabled_features.get(name, True):
            raise AttributeError(f"Feature '{name}' is disabled")

        if name not in self._instances:
            cls = self.feature_overrides.get(name, _ALL_FEATURES[name])
            self._instances[name] = cls(dims=self.dims)  # type: ignore[arg-type]

        return self._instances[name]

    def feature(self, name: str) -> ArenaFeature:
        return self._get_feature(name)

    def geometry(self) -> Sequence[object]:
        self._refresh_feature_catalog()
        if self._geom_cache is None:
            geo: List[object] = []
            feature_names = list(_ALL_FEATURES)

            for name in feature_names:
                if self.enabled_features.get(name, True):
                    geo.extend(self._get_feature(name).geometry())

            self._geom_cache = tuple(geo)

        return self._geom_cache

    def collision_surfaces(self) -> Sequence[object]:
        self._refresh_feature_catalog()
        if self._collision_cache is None:
            coll: List[object] = []
            feature_names = list(_ALL_FEATURES)

            for name in feature_names:
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
        self._refresh_feature_catalog()
        feature_names = list(_ALL_FEATURES)
        for name in feature_names:
            if self.enabled_features.get(name, True):
                yield self._get_feature(name)

    def __repr__(self) -> str:
        active = ", ".join(
            n for n, on in self.enabled_features.items() if on
        )

        return f"<Rink features=[{active}] dims={self.dims}>"
