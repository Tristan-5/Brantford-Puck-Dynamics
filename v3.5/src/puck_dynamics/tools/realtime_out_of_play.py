from __future__ import annotations

import argparse
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from puck_dynamics.arena import Rink
from puck_dynamics.simulation.seating_grid import SeatingGrid
from puck_dynamics.simulation.simulator import Simulator


@dataclass(slots=True)
class LandingPoint:
    x: float
    y: float
    t: float


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render live out-of-play landing points over baseline.png in real time.",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path(__file__).with_name("sensitivity_images") / "baseline.png",
        help="Path to baseline.png used as the exact background.",
    )
    parser.add_argument(
        "--blank-heatmap",
        action="store_true",
        help="Use a blank background with baseline sizing/layout but without the heatmap pixels.",
    )
    parser.add_argument(
        "--shots-per-second",
        type=float,
        default=14.0,
        help="How many simulated shots to process per second.",
    )
    parser.add_argument(
        "--max-points",
        type=int,
        default=5000,
        help="Maximum number of visible points kept in memory.",
    )
    parser.add_argument(
        "--point-radius",
        type=int,
        default=3,
        help="Point radius in pixels.",
    )
    parser.add_argument(
        "--point-color",
        type=str,
        default="120,255,255,180",
        help="Point RGBA as comma-separated integers, e.g. 120,255,255,180.",
    )
    parser.add_argument(
        "--trail-seconds",
        type=float,
        default=0.0,
        help="If > 0, fade out points older than this many seconds.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=17,
        help="Random seed for reproducibility.",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=60,
        help="Target render FPS.",
    )
    return parser.parse_args()


def _parse_rgba(text: str) -> tuple[int, int, int, int]:
    parts = [p.strip() for p in text.split(",")]
    if len(parts) != 4:
        raise ValueError("--point-color must contain 4 comma-separated values (R,G,B,A).")
    vals = tuple(int(v) for v in parts)
    for v in vals:
        if v < 0 or v > 255:
            raise ValueError("RGBA values must each be in [0, 255].")
    return vals  # type: ignore[return-value]


def _build_world_to_screen_mapper(
    baseline_path: Path,
    grid: SeatingGrid,
    blank_heatmap: bool = False,
):
    # Use matplotlib's data transform with the same heatmap layout logic,
    # then draw in pygame on the unscaled baseline.png.
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import PowerNorm
    from matplotlib.patches import Polygon

    img = plt.imread(str(baseline_path))
    if img.ndim < 2:
        raise RuntimeError(f"Could not read baseline image: {baseline_path}")
    height_px, width_px = int(img.shape[0]), int(img.shape[1])

    fig = plt.figure(figsize=(width_px / 250.0, height_px / 250.0), dpi=250)
    ax = fig.add_subplot(111)

    im = None
    if not blank_heatmap:
        # Build a dummy plotted field with the same draw path used for baseline.
        dummy = np.zeros(grid.shape, dtype=np.float64)
        plotted = grid.smooth_probabilities(dummy, sigma_m=1.25)
        outside_mask = np.ones_like(plotted, dtype=bool)
        for ix in range(plotted.shape[0]):
            x = grid.bounds.x_min + (ix + 0.5) * grid.dx
            for iy in range(plotted.shape[1]):
                y = grid.bounds.y_min + (iy + 0.5) * grid.dy
                if grid._point_is_inside_rink(x, y):
                    plotted[ix, iy] = np.nan
                    outside_mask[ix, iy] = False

        if np.any(outside_mask):
            plotted[outside_mask] = 1e-12
            norm_total = np.nansum(plotted[outside_mask])
            if norm_total > 0:
                plotted[outside_mask] = plotted[outside_mask] / norm_total

        cmap = plt.get_cmap("inferno").copy()
        cmap.set_bad("white", alpha=1.0)
        im = ax.imshow(
            plotted.T,
            origin="lower",
            extent=[grid.bounds.x_min, grid.bounds.x_max, grid.bounds.y_min, grid.bounds.y_max],
            cmap=cmap,
            interpolation="nearest",
            norm=PowerNorm(gamma=0.55, vmin=0.0),
        )
    else:
        # Keep world extents identical while omitting heatmap pixels.
        ax.set_xlim(grid.bounds.x_min, grid.bounds.x_max)
        ax.set_ylim(grid.bounds.y_min, grid.bounds.y_max)
        ax.set_facecolor("white")

    outline = None
    try:
        from puck_dynamics.arena.dimensions import NHLStandardDimensions
        from puck_dynamics.tools.render_rink_trimesh import make_rink_outline

        outline_poly = make_rink_outline(NHLStandardDimensions())
        outline = list(outline_poly.exterior.coords)
    except Exception:
        pass

    if outline is None:
        x0, x1, y0, y1 = grid.rink_overlay_bounds()
        outline = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

    fill_patch = Polygon(
        outline,
        closed=True,
        facecolor="white",
        edgecolor="none",
        linewidth=0.0,
        antialiased=False,
        zorder=5,
    )
    outline_patch = Polygon(
        outline,
        closed=True,
        facecolor="none",
        edgecolor="black",
        linewidth=0.8,
        antialiased=False,
        zorder=6,
    )
    ax.add_patch(fill_patch)
    ax.add_patch(outline_patch)

    if im is not None:
        fig.colorbar(im, ax=ax, label="Souvenir probability (hits / shots)")
    ax.set_title("Predicted souvenir-puck landing density")
    ax.set_aspect("equal", adjustable="box")

    fig.canvas.draw()
    trans = ax.transData
    canvas_rgba = np.asarray(fig.canvas.buffer_rgba()).copy()

    def world_to_screen(x_m: float, y_m: float) -> tuple[int, int]:
        x_px, y_px = trans.transform((x_m, y_m))
        return int(round(x_px)), int(round(height_px - y_px))

    plt.close(fig)
    return world_to_screen, width_px, height_px, canvas_rgba


def _simulate_out_of_play(sim: Simulator):
    while True:
        traj = sim._run_single()  # Script-level use for real-time visualization.
        sim.world.pucks.clear()
        if traj.landed and traj.out_of_play and traj.final_pos is not None:
            return traj.final_pos


def main() -> None:
    args = _parse_args()
    rgba = _parse_rgba(args.point_color)

    baseline_path = args.baseline.resolve()
    if not baseline_path.exists():
        raise FileNotFoundError(f"Baseline image not found: {baseline_path}")

    random.seed(args.seed)
    np.random.seed(args.seed)

    rink = Rink()
    grid = SeatingGrid.outside_rink(rink, dx=0.25, dy=0.25, margin=40.0)
    sim = Simulator(rink=rink, shots=1, record_path=False)
    world_to_screen, width_px, height_px, generated_background = _build_world_to_screen_mapper(
        baseline_path,
        grid,
        blank_heatmap=args.blank_heatmap,
    )

    try:
        import pygame
    except ImportError as exc:
        raise RuntimeError(
            "pygame is required for this viewer. Install it with: pip install pygame"
        ) from exc

    pygame.init()
    screen = pygame.display.set_mode((width_px, height_px))
    pygame.display.set_caption("Out-of-play puck landings (real-time)")

    if args.blank_heatmap:
        baseline = pygame.image.frombuffer(
            generated_background.tobytes(),
            (width_px, height_px),
            "RGBA",
        ).convert()
    else:
        baseline = pygame.image.load(str(baseline_path)).convert()

    point_layer = pygame.Surface((width_px, height_px), flags=pygame.SRCALPHA)
    clock = pygame.time.Clock()

    points: list[LandingPoint] = []
    dt_shot = 1.0 / max(1e-6, args.shots_per_second)
    shot_accum = 0.0
    prev_t = time.perf_counter()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        now = time.perf_counter()
        frame_dt = now - prev_t
        prev_t = now
        shot_accum += frame_dt

        while shot_accum >= dt_shot:
            shot_accum -= dt_shot
            landed = _simulate_out_of_play(sim)
            points.append(LandingPoint(x=landed.x, y=landed.y, t=now))
            if len(points) > args.max_points:
                points = points[-args.max_points :]

        if args.trail_seconds > 0.0:
            cutoff = now - args.trail_seconds
            points = [point for point in points if point.t >= cutoff]

        point_layer.fill((0, 0, 0, 0))
        if args.trail_seconds > 0.0:
            for point in points:
                age = now - point.t
                fade = max(0.0, 1.0 - age / args.trail_seconds)
                alpha = int(rgba[3] * fade)
                if alpha <= 0:
                    continue
                sx, sy = world_to_screen(point.x, point.y)
                pygame.draw.circle(
                    point_layer,
                    (rgba[0], rgba[1], rgba[2], alpha),
                    (sx, sy),
                    args.point_radius,
                )
        else:
            for point in points:
                sx, sy = world_to_screen(point.x, point.y)
                pygame.draw.circle(
                    point_layer,
                    rgba,
                    (sx, sy),
                    args.point_radius,
                )

        # Keep the baseline pixels untouched as the base layer for easy video overlay.
        screen.blit(baseline, (0, 0))
        screen.blit(point_layer, (0, 0))
        pygame.display.flip()
        clock.tick(max(1, args.fps))

    pygame.quit()


if __name__ == "__main__":
    main()