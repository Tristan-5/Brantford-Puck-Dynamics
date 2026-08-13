from puck_dynamics.arena.rink import Rink
from puck_dynamics.geometry import Cylinder
from matplotlib.path import Path as MplPath
import numpy as np
from puck_dynamics.tools import render_rink_3d as rr

r = Rink()
# build rink polygon
rink_poly = None
for f in r.features():
    if getattr(f, 'name', None) == 'rink_surface':
        for g in f.geometry():
            try:
                pts = g.discretize(512)
            except Exception:
                pts = getattr(g, 'points', None)
            if pts:
                rink_poly = [(p.x, p.y) for p in pts]
                break
        if rink_poly:
            break
path = MplPath(rink_poly) if rink_poly is not None else None

print('Found rink polygon:', bool(rink_poly))
count = 0
for f in r.features():
    for g in f.geometry():
        if isinstance(g, Cylinder):
            cx = g.base_center.x
            cy = g.base_center.y
            rads = g.radius
            segs = rr.outside_theta_segments(cx, cy, rads, path, segments=256)
            print(getattr(f, 'name', None), 'center', (cx, cy), 'r', rads, 'segs', len(segs))
            count += 1
print('total cylinders', count)
