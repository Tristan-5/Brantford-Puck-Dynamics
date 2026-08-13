import sys
import pathlib
import unittest

root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root.parent))

from puck_dynamics.arena.features.rink_surface import RinkSurface
from puck_dynamics.geometry import AABB, Box3D, Plane3D
from puck_dynamics.geometry.point import Point3D
from puck_dynamics.simulation.seating_grid import SeatingGrid
from puck_dynamics.simulation.simulator import Simulator


class AABBCompatibilityTests(unittest.TestCase):
    def test_from_bounds_creates_box(self) -> None:
        box = Box3D.from_bounds(x_min=0.0, x_max=1.0, y_min=2.0, y_max=3.0, z_min=4.0, z_max=5.0)
        self.assertIsInstance(box, AABB)
        self.assertEqual(box.min_pt, Point3D(0.0, 2.0, 4.0))
        self.assertEqual(box.max_pt, Point3D(1.0, 3.0, 5.0))

    def test_aabb_helpers_support_grid_logic(self) -> None:
        box = Box3D.from_bounds(x_min=0.0, x_max=2.0, y_min=1.0, y_max=3.0, z_min=0.0, z_max=1.0)
        self.assertIs(box.aabb, box)
        self.assertTrue(box.contains_xy(Point3D(1.0, 2.0, 0.5)))
        self.assertFalse(box.contains_xy(Point3D(3.0, 2.0, 0.5)))
        merged = AABB.union([box, Box3D.from_bounds(x_min=3.0, x_max=4.0, y_min=0.0, y_max=1.0, z_min=0.0, z_max=1.0)])
        self.assertEqual(merged.x_min, 0.0)
        self.assertEqual(merged.x_max, 4.0)

    def test_point_copy_returns_independent_instance(self) -> None:
        point = Point3D(1.0, 2.0, 3.0)
        copied = point.copy()
        self.assertEqual(copied, point)
        self.assertIsNot(copied, point)

    def test_rink_surface_plane_matches_playing_surface(self) -> None:
        surface = RinkSurface()
        plane = next(geom for geom in surface.geometry() if isinstance(geom, Plane3D))
        self.assertAlmostEqual(plane.width, surface.dims.length)
        self.assertAlmostEqual(plane.height, surface.dims.width)

    def test_simulator_can_accumulate_out_of_play_probabilities(self) -> None:
        from puck_dynamics.arena import Rink

        rink = Rink()
        grid = SeatingGrid.outside_rink(rink, dx=2.0, dy=2.0, margin=12.0)
        sim = Simulator(rink=rink, shots=5, record_path=False)

        probs = sim.run_out_of_play_grid(grid, progress=False)

        self.assertEqual(probs.shape, grid.shape)
        self.assertGreaterEqual(probs.sum(), 0.0)


if __name__ == "__main__":
    unittest.main()
