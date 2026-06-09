# Brantford Puck Dynamics

A simulation framework for modeling out-of-play puck trajectories in an ice hockey arena.

## Current scope

This repository starts as a modular stochastic simulation scaffold. Te goal is to:
- sample realistic shot origins and velocities,
- propagate puck trajectories through a simplified rink geometry,
- handle events such as glass reflection, deflection and absorption by netting,
- aggregate landing points into heatmaps and summary statistics.

## Project layout

- `src/puck_dynamics/physics/`: kinematics and trajectory updates
- `src/puck_dynamics/distributions/`: sampling distributions for shots and deflections
- `src/puck_dynamics/events/`: event handlers for collisions and boundaries
- `src/puck_dynamics/arena/`: rink geometry and zone definitions
- `src/puck_dynamics/simulation/`: simulation engine and runner
- `src/puck_dynamics/analysis/`: heatmaps, statistics, and risk metrics
- `experiments/`: reproducible entry points for individual studies
- `paper/`: LaTeX draft for the preprint
- `data-entry-portal/`: schema notes for future manual logging
