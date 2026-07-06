from __future__ import annotations
from typing import Sequence
from puck_dynamics.geometry import AABB

class Node:
    __slots__ = ("aabb", "left", "right", "items")
    def __init__(self, items: Sequence[object], axis: int = 0):
        if len(items) <= 6:
            self.items = list(items)
            self.left = self.right = None
        else:
            items = list(items)
            items.sort(key=lambda s: s.aabb.center()[axis])
            mid = len(items)//2
            self.left  = Node(items[:mid], (axis+1)%3)
            self.right = Node(items[mid:], (axis+1)%3)
            self.items = []
        # union AABB
        boxes = [s.aabb for s in items]
        self.aabb = AABB.union(boxes)

    def query(self, sphere_center, sphere_rad, out):
        if not self.aabb.intersects_sphere(sphere_center, sphere_rad):
            return
        for it in self.items:
            if it.aabb.intersects_sphere(sphere_center, sphere_rad):
                out.append(it)
        if self.left:  self.left.query(sphere_center, sphere_rad, out)
        if self.right: self.right.query(sphere_center, sphere_rad, out)
