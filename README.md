# Heatmap Simulation

This repository is currently documented as a heatmap simulation project for out-of-play puck landing probability.

The core workflow is:

1. Simulate many shots with Monte Carlo sampling.
2. Collect out-of-play landing points in rink-centered coordinates.
3. Bin landings into a 2D grid.
4. Smooth and normalize the grid into a probability heatmap.
5. Save image and array artifacts for reporting and downstream analysis.

## Requirements

Tested on Windows with Python 3.10+.

Install required packages:

```powershell
python -m pip install numpy matplotlib tqdm
```

## Quick Start

Run all commands from the repository root.

### 1) Generate a baseline heatmap

```powershell
python src/puck_dynamics/run_simulation.py
```

Output:

- `src/puck_dynamics/heatmap.png`

### 2) Generate out-of-play probability artifacts

```powershell
python src/puck_dynamics/tools/out_of_play_probabilities.py
```

Outputs:

- `src/puck_dynamics/tools/out_of_play_probabilities.npy`
- `src/puck_dynamics/tools/out_of_play_probabilities.png`

This script also prints top-probability cells in rink coordinates.

### 3) Run a scenario sweep

```powershell
python src/puck_dynamics/tools/sensitivity_sweep.py --shots 12000
```

Outputs:

- Scenario arrays and images in `src/puck_dynamics/tools/sensitivity_images/`
- An overview figure (default: `sensitivity_overview.png`)

Useful options:

- `--shots`: samples per scenario
- `--seed`: reproducibility seed
- `--overview-sigma`: smoothing strength in meters
- `--overview-interp`: `nearest`, `bilinear`, or `bicubic`
- `--overview-style`: `standard` or `minimal`

## Heatmap Pipeline

1. `src/puck_dynamics/simulation/shot_sampler.py`
: Samples shot type, release point, speed, elevation, azimuth, and spin.

2. `src/puck_dynamics/simulation/simulator.py`
: Runs physics ticks, classifies out-of-play exits, and projects landing points.

3. `src/puck_dynamics/simulation/seating_grid.py`
: Maps world coordinates to grid indices, smooths probabilities, and saves heatmaps.

4. `src/puck_dynamics/simulation/heatmap.py`
: Accumulates and normalizes hit counts.

## Main Tuning Knobs

- `ShotSamplingConfig` in `src/puck_dynamics/simulation/shot_sampler.py`
: Controls zone weights, azimuth spread, and release tendencies.

- `LandingModelConfig` in `src/puck_dynamics/simulation/simulator.py`
: Controls runout/deceleration, retention, and crowd-depth assumptions.

- `SeatingGrid.outside_rink(..., dx, dy, margin)` in `src/puck_dynamics/simulation/seating_grid.py`
: Controls spatial resolution and analysis extents.

## Validation

Run the included test module:

```powershell
python -m unittest src/puck_dynamics/tests/test_geometry.py
```

## Notes

- Units are meters throughout the simulation.
- Scripts include path bootstrapping, so running by file path from repo root works.
- Repo will be updated with the newest code soon in a seperate folder.
