from __future__ import annotations

import argparse
import math
import random
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from puck_dynamics.arena import Rink
from puck_dynamics.arena.dimensions import NHLStandardDimensions, ft_to_m
from puck_dynamics.simulation.seating_grid import SeatingGrid
from puck_dynamics.simulation.shot_sampler import ShotSamplingConfig
from puck_dynamics.simulation.simulator import (
    LandingModelConfig,
    Simulator,
)


def _slug(name: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in name).strip("_")


def _run_case(
    name: str,
    shot_config: ShotSamplingConfig,
    landing_config: LandingModelConfig,
    out_dir: Path,
    shots: int,
    seed: int,
) -> None:
    print(f"running: {name}", flush=True)
    random.seed(seed)
    np.random.seed(seed)

    rink = Rink()
    grid = SeatingGrid.outside_rink(rink, dx=0.25, dy=0.25, margin=40.0)
    sim = Simulator(
        rink=rink,
        shots=shots,
        record_path=False,
        shot_config=shot_config,
        landing_config=landing_config,
    )

    raw_probs = sim.run_out_of_play_grid(grid, progress=False)
    probs = grid.debias_symmetry(raw_probs, blend=0.65)

    slug = _slug(name)
    npy_path = out_dir / f"{slug}.npy"
    png_path = out_dir / f"{slug}.png"
    np.save(npy_path, probs)
    grid.save_outside_rink_heatmap(probs, str(png_path))

    flat = np.argwhere(probs > 0.0)
    if flat.size:
        best = max(flat, key=lambda idx: probs[tuple(idx)])
        ix, iy = int(best[0]), int(best[1])
        x = grid.bounds.x_min + (ix + 0.5) * grid.dx
        y = grid.bounds.y_min + (iy + 0.5) * grid.dy
        print(f"{name:30s} peak=({x:6.2f}, {y:6.2f}) max={probs[ix, iy]:.6e}")
    else:
        print(f"{name:30s} no out-of-play bins")


def _save_overview_chart(
    out_dir: Path,
    series: list[tuple[str, np.ndarray]],
    grid: SeatingGrid,
    sigma_m: float = 2.2,
    interpolation: str = "bicubic",
    style: str = "standard",
    output_name: str = "sensitivity_overview.png",
) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm
    from matplotlib.patches import Polygon, Circle

    if not series:
        return

    vmin = 0.0

    cols = 3
    rows = int(np.ceil(len(series) / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(4.3 * cols, 3.9 * rows), constrained_layout=True)
    axes = np.atleast_1d(axes).ravel()

    extent = [
        grid.bounds.x_min,
        grid.bounds.x_max,
        grid.bounds.y_min,
        grid.bounds.y_max,
    ]

    # Clip off the darkest inferno tail so low probabilities are still visible.
    cmap = plt.cm.colors.LinearSegmentedColormap.from_list(
        "inferno_warm_low",
        plt.get_cmap("inferno")(np.linspace(0.16, 1.0, 256)),
    )
    cmap.set_bad("white", alpha=1.0)

    dims = NHLStandardDimensions()
    half_len = dims.length / 2.0
    half_wid = dims.width / 2.0
    r = dims.corner_radius
    outline: list[tuple[float, float]] = []

    outline.append((half_len, -half_wid + r))
    outline.append((half_len, half_wid - r))

    cx, cy = half_len - r, half_wid - r
    arc_steps = 96

    for i in range(arc_steps + 1):
        theta = 0.0 + i * (math.pi / 2.0) / arc_steps
        outline.append((cx + r * math.cos(theta), cy + r * math.sin(theta)))

    outline.append((half_len - r, half_wid))
    outline.append((-half_len + r, half_wid))

    cx, cy = -half_len + r, half_wid - r
    for i in range(arc_steps + 1):
        theta = math.pi / 2.0 + i * (math.pi / 2.0) / arc_steps
        outline.append((cx + r * math.cos(theta), cy + r * math.sin(theta)))

    outline.append((-half_len, half_wid - r))
    outline.append((-half_len, -half_wid + r))

    cx, cy = -half_len + r, -half_wid + r
    for i in range(arc_steps + 1):
        theta = math.pi + i * (math.pi / 2.0) / arc_steps
        outline.append((cx + r * math.cos(theta), cy + r * math.sin(theta)))

    outline.append((-half_len + r, -half_wid))
    outline.append((half_len - r, -half_wid))

    cx, cy = half_len - r, -half_wid + r
    for i in range(arc_steps + 1):
        theta = 3.0 * math.pi / 2.0 + i * (math.pi / 2.0) / arc_steps
        outline.append((cx + r * math.cos(theta), cy + r * math.sin(theta)))

    blue_line_width = ft_to_m(1.0)
    center_line_width = ft_to_m(1.0)
    goal_line_width = ft_to_m(2.0 / 12.0)
    blue_near = dims.blue_line_distance
    x_blue_w = -half_len + blue_near + blue_line_width / 2.0
    x_blue_e = +half_len - blue_near - blue_line_width / 2.0
    x_goal = +half_len - dims.goal_line_distance
    faceoff_r = ft_to_m(15.0)
    end_spot_y = ft_to_m(22.0) / 2.0
    end_spot_x = x_goal - ft_to_m(20.0)

    # Build display arrays first so the color scale reflects what we actually render.
    display_arrays: list[np.ndarray] = []
    for _, probs in series:
        plotted = grid.smooth_probabilities(probs, sigma_m=sigma_m).copy()
        outside_mask = np.ones_like(plotted, dtype=bool)
        for ix in range(plotted.shape[0]):
            x = grid.bounds.x_min + (ix + 0.5) * grid.dx
            for iy in range(plotted.shape[1]):
                y = grid.bounds.y_min + (iy + 0.5) * grid.dy
                if grid._point_is_inside_rink(x, y):
                    plotted[ix, iy] = np.nan
                    outside_mask[ix, iy] = False

        # Match single heatmap behavior: add a small floor to make tails visible.
        if np.any(outside_mask):
            finite = plotted[outside_mask]
            peak = float(np.nanmax(finite)) if finite.size else 0.0
            floor = max(peak * 0.012, 1e-12)
            plotted[outside_mask] = plotted[outside_mask] + floor
            norm_total = np.nansum(plotted[outside_mask])
            if norm_total > 0:
                plotted[outside_mask] = plotted[outside_mask] / norm_total

        display_arrays.append(plotted)

    finite_values = [arr[np.isfinite(arr)] for arr in display_arrays if np.any(np.isfinite(arr))]
    if finite_values:
        finite_all = np.concatenate(finite_values)
        positive_all = finite_all[finite_all > 0.0]
        if positive_all.size:
            vmax = float(np.quantile(positive_all, 0.995))
            vmin = float(np.quantile(positive_all, 0.15))
        else:
            vmax = 1e-12
            vmin = 1e-12
    else:
        vmax = 1e-12
        vmin = 1e-12
    vmax = max(vmax, 1e-12)
    vmin = max(min(vmin, vmax * 0.5), 1e-12)

    style_key = style.strip().lower()
    minimal_style = style_key == "minimal"

    mappable = None
    for ax, (name, _), plotted in zip(axes, series, display_arrays):

        mappable = ax.imshow(
            plotted.T,
            origin="lower",
            extent=extent,
            cmap=cmap,
            interpolation=interpolation,
            norm=LogNorm(vmin=vmin, vmax=vmax),
        )

        fill_patch = Polygon(
            outline,
            closed=True,
            facecolor="white",
            edgecolor="none",
            linewidth=0.0,
            antialiased=True,
            zorder=5,
        )
        outline_patch = Polygon(
            outline,
            closed=True,
            facecolor="none",
            edgecolor="#222222" if minimal_style else "black",
            linewidth=0.55 if minimal_style else 0.8,
            antialiased=True,
            joinstyle="round",
            zorder=6,
        )
        ax.add_patch(fill_patch)
        ax.add_patch(outline_patch)

        if not minimal_style:
            line_bands = [
                ax.axvspan(-center_line_width / 2.0, center_line_width / 2.0, color="#c62828", alpha=0.75, zorder=7),
                ax.axvspan(x_blue_w - blue_line_width / 2.0, x_blue_w + blue_line_width / 2.0, color="#1e4db7", alpha=0.8, zorder=7),
                ax.axvspan(x_blue_e - blue_line_width / 2.0, x_blue_e + blue_line_width / 2.0, color="#1e4db7", alpha=0.8, zorder=7),
                ax.axvspan(-x_goal - goal_line_width / 2.0, -x_goal + goal_line_width / 2.0, color="#d32f2f", alpha=0.7, zorder=7),
                ax.axvspan(x_goal - goal_line_width / 2.0, x_goal + goal_line_width / 2.0, color="#d32f2f", alpha=0.7, zorder=7),
            ]
            for band in line_bands:
                band.set_clip_path(fill_patch)

            circles = [
                (0.0, 0.0),
                (+end_spot_x, +end_spot_y),
                (+end_spot_x, -end_spot_y),
                (-end_spot_x, +end_spot_y),
                (-end_spot_x, -end_spot_y),
            ]
            for cx, cy in circles:
                circle = Circle(
                    (cx, cy),
                    radius=faceoff_r,
                    facecolor="none",
                    edgecolor="#1e4db7",
                    linewidth=1.0,
                    alpha=0.85,
                    zorder=8,
                )
                circle.set_clip_path(fill_patch)
                ax.add_patch(circle)

        ax.set_title(name.replace("_", " "))
        ax.set_xlabel("x (m)")
        ax.set_ylabel("y (m)")
        ax.set_aspect("equal", adjustable="box")

    for ax in axes[len(series):]:
        ax.axis("off")

    if mappable is not None:
        fig.colorbar(mappable, ax=axes.tolist(), label="Souvenir probability (hits / shots)")

    out_path = out_dir / output_name
    fig.savefig(out_path, dpi=250)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate sensitivity heatmaps for lobe-position analysis.")
    parser.add_argument("--shots", type=int, default=12000, help="Shots per scenario (default: 12000)")
    parser.add_argument("--seed", type=int, default=17, help="Base random seed (default: 17)")
    parser.add_argument(
        "--overview-sigma",
        type=float,
        default=2.2,
        help="Smoothing sigma in meters for sensitivity_overview.png (default: 2.2)",
    )
    parser.add_argument(
        "--overview-interp",
        type=str,
        default="bicubic",
        choices=("nearest", "bilinear", "bicubic"),
        help="Interpolation for sensitivity_overview.png (default: bicubic)",
    )
    parser.add_argument(
        "--overview-style",
        type=str,
        default="standard",
        choices=("standard", "minimal"),
        help="Visual style for sensitivity_overview output (default: standard)",
    )
    parser.add_argument(
        "--overview-output",
        type=str,
        default="sensitivity_overview.png",
        help="Filename for overview output image (default: sensitivity_overview.png)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).with_name("sensitivity_images"),
        help="Output directory for PNG/NPY files",
    )
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    shots = max(1000, int(args.shots))
    base_shot = ShotSamplingConfig()
    base_land = LandingModelConfig()

    cases = [
        ("baseline", base_shot, base_land),
        (
            "more_neutral_zone",
            replace(base_shot, offensive_weight=0.58, neutral_weight=0.30, deflection_weight=0.12),
            base_land,
        ),
        (
            "wider_offensive_azimuth",
            replace(base_shot, offensive_azim_sigma_deg=32.0),
            base_land,
        ),
        (
            "more_lateral_neutral",
            replace(base_shot, neutral_lateral_sigma_deg=18.0, neutral_forward_sigma_deg=38.0),
            base_land,
        ),
        (
            "longer_runout",
            base_shot,
            replace(base_land, decel_min=9.5, decel_max=16.0, crowd_depth_mode=11.0, crowd_depth_max=24.0),
        ),
        (
            "shorter_runout",
            base_shot,
            replace(base_land, decel_min=16.0, decel_max=24.0, crowd_depth_mode=6.0, crowd_depth_max=14.0),
        ),
    ]

    series: list[tuple[str, np.ndarray]] = []
    preview_grid = SeatingGrid.outside_rink(Rink(), dx=0.25, dy=0.25, margin=40.0)

    for i, (name, shot_cfg, land_cfg) in enumerate(cases):
        _run_case(
            name=name,
            shot_config=shot_cfg,
            landing_config=land_cfg,
            out_dir=out_dir,
            shots=shots,
            seed=args.seed + i,
        )
        arr = np.load(out_dir / f"{_slug(name)}.npy")
        series.append((name, arr))

    _save_overview_chart(
        out_dir,
        series,
        preview_grid,
        sigma_m=max(0.5, float(args.overview_sigma)),
        interpolation=args.overview_interp,
        style=args.overview_style,
        output_name=args.overview_output,
    )

    print("saved_dir", out_dir)


if __name__ == "__main__":
    main()
