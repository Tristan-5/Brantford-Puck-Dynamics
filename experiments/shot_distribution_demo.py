
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

"""Visualize the offensive-zone shot-origin distribution."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np

from puck_dynamics.arena.geometry import RinkGeometry
from puck_dynamics.arena.zones import default_shot_zones
from puck_dynamics.distributions.shot_distribution import sample_shot_origin


def _draw_rink(ax, geom: RinkGeometry) -> None:
    ax.add_patch(Rectangle((0, 0), geom.length_m, geom.width_m, fill=False, linewidth=2))
    ax.axvline(geom.offensive_zone_x_min, linestyle='--', linewidth=1)
    ax.axvline(geom.netting_x, linestyle=':', linewidth=1)

    # Goal line and net region
    ax.plot([geom.goal_x, geom.goal_x], [geom.goal_y - 1.0, geom.goal_y + 1.0], linewidth=3)
    ax.add_patch(
        Rectangle(
            (geom.netting_x, geom.netting_y_min),
            geom.length_m - geom.netting_x,
            geom.netting_y_max - geom.netting_y_min,
            fill=False,
            hatch='//',
            alpha=0.5,
            linewidth=1.5,
        )
    )

    # Shot-zone centers
    for zone in default_shot_zones(geom):
        ax.scatter([zone.center_x], [zone.center_y], marker='x', s=80)
        ax.text(zone.center_x + 0.4, zone.center_y + 0.4, zone.name, fontsize=9)


def main() -> None:
    geom = RinkGeometry()
    rng = np.random.default_rng(42)
    points = np.array([sample_shot_origin(rng, geom=geom)[:2] for _ in range(10_000)], dtype=float)

    fig, ax = plt.subplots(figsize=(12, 6))
    _draw_rink(ax, geom)
    ax.scatter(points[:, 0], points[:, 1], s=4, alpha=0.18)
    ax.set_xlim(geom.offensive_zone_x_min - 2, geom.length_m + 1)
    ax.set_ylim(0, geom.width_m)
    ax.set_aspect('equal', adjustable='box')
    ax.set_xlabel('x (m)')
    ax.set_ylabel('y (m)')
    ax.set_title('Sampled Offensive-Zone Shot Origins')
    ax.grid(alpha=0.15)

    out_dir = Path('figures/heatmaps')
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / 'offensive_zone_sampling.png'
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    print(f'Saved {out_path}')


if __name__ == '__main__':
    main()
