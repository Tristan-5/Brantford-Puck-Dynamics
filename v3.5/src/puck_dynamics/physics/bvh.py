from __future__ import annotations
from typing import Sequence
from puck_dynamics.geometry import AABB


def _surface_aabb(surface: object) -> AABB:
    aabb = getattr(surface, "aabb", None)
    if aabb is not None:
        return aabb
    if hasattr(surface, "bounds"):
        return surface.bounds()
    if hasattr(surface, "min_pt") and hasattr(surface, "max_pt"):
        return AABB(surface.min_pt, surface.max_pt)
    if hasattr(surface, "center") and hasattr(surface, "radius"):
        center = surface.center()
        radius = surface.radius
        return AABB.from_center_halfsizes(center, (radius, radius, radius))
    raise AttributeError(f"Surface {surface!r} has no AABB or bounds")


class Node:
    __slots__ = ("aabb", "left", "right", "items")
    def __init__(self, items: Sequence[object], axis: int = 0):
        if len(items) <= 6:
            self.items = list(items)
            self.left = self.right = None
        else:
            items = list(items)
            items.sort(key=lambda s: _surface_aabb(s).center()[axis])
            mid = len(items)//2
            self.left  = Node(items[:mid], (axis+1)%3)
            self.right = Node(items[mid:], (axis+1)%3)
            self.items = []
        # union AABB
        boxes = [_surface_aabb(s) for s in items]
        self.aabb = AABB.union(boxes)

    def query(self, sphere_center, sphere_rad, out):
        if not self.aabb.intersects_sphere(sphere_center, sphere_rad):
            return
        for it in self.items:
            if _surface_aabb(it).intersects_sphere(sphere_center, sphere_rad):
                out.append(it)
        if self.left:  self.left.query(sphere_center, sphere_rad, out)
        if self.right: self.right.query(sphere_center, sphere_rad, out)
