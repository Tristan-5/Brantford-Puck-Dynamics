from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Iterable, List, Sequence

from puck_dynamics.geometry import AABB, Transform  # type: ignore[attr-defined]


@dataclass(frozen=True, slots=True)
class ArenaFeature(abc.ABC):

    name: str = field(metadata={"doc": "Human-readable identifier"})

    @abc.abstractmethod
    def geometry(self) -> Sequence[object]:



    def bounds(self) -> AABB:

        primitives: Iterable[object] = self.geometry()
        it = iter(primitives)
        try:
            aabb = next(it).bounds()  # type: ignore[attr-defined]
        except StopIteration:  # pragma: no cover
            raise ValueError(f"{self.name} contains no geometry.")
        for g in it:
            aabb = aabb.union(g.bounds())  # type: ignore[attr-defined]
        return aabb

    def collision_surfaces(self) -> Sequence[object]:

        return self.geometry()

    def draw(self, renderer, *args, **kwargs):

        renderer.draw_feature(self, *args, **kwargs)


class ArenaComposite(ArenaFeature):

    _children: List[ArenaFeature] = field(
        default_factory=list, metadata={"doc": "Ordered child features"}
    )


    def geometry(self) -> Sequence[object]:
        """
        Flattens geometry from all child features.
        """
        geom = []
        for child in self._children:
            geom.extend(child.geometry())
        return geom

    def collision_surfaces(self) -> Sequence[object]:
        cs = []
        for child in self._children:
            cs.extend(child.collision_surfaces())
        return cs

    def __iter__(self):
        yield from self._children

    def __getitem__(self, idx: int) -> ArenaFeature:
        return self._children[idx]
