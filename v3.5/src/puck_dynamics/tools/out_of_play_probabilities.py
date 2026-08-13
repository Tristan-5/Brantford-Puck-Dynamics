from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np

from puck_dynamics.arena import Rink
from puck_dynamics.simulation.seating_grid import SeatingGrid
from puck_dynamics.simulation.simulator import Simulator


def main() -> None:
    rink = Rink()
    grid = SeatingGrid.outside_rink(rink, dx=0.25, dy=0.25, margin=40.0)
    sim = Simulator(rink=rink, shots=16_000, record_path=False)

    raw_probs = sim.run_out_of_play_grid(grid, progress=False)
    probs = grid.debias_symmetry(raw_probs, blend=0.65)

    out_path = Path(__file__).with_name("out_of_play_probabilities.npy")
    image_path = Path(__file__).with_name("out_of_play_probabilities.png")
    np.save(out_path, probs)
    grid.save_outside_rink_heatmap(probs, str(image_path))

    # Print the most likely cells in rink-centered coordinates.
    flat = np.argwhere(probs > 0.0)
    if flat.size:
        best = sorted(flat, key=lambda idx: probs[tuple(idx)], reverse=True)[:10]
        print("shape", probs.shape)
        print("sum", probs.sum())
        print("max", probs.max())
        print("top_cells")
        for idx in best:
            ix, iy = int(idx[0]), int(idx[1])
            x = grid.bounds.x_min + (ix + 0.5) * grid.dx
            y = grid.bounds.y_min + (iy + 0.5) * grid.dy
            print(f"  ({x:.2f}, {y:.2f}) -> {probs[ix, iy]:.4f}")
    else:
        print("no out-of-play cells recorded")

    print("saved", out_path)
    print("saved_image", image_path)


if __name__ == "__main__":
    main()
