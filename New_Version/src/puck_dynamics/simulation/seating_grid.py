from __future__ import annotations
import numpy as np
from puck_dynamics.geometry import AABB, Point3D as Vec
from puck_dynamics.arena import Rink, Seating

class SeatingGrid:
    def __init__(self,
                 bounds: AABB,
                 dx: float = 1.0,
                 dy: float = 1.0) -> None:
        self.bounds = bounds
        self.dx = dx
        self.dy = dy
        nx = int(np.ceil(bounds.width  / dx))
        ny = int(np.ceil(bounds.height / dy))
        self.shape = (nx, ny)

    def index_of(self, p: Vec) -> tuple[int, int] | None:
        """Return (ix, iy) or None if outside grid."""
        if not self.bounds.contains_xy(p):
            return None
        ix = int((p.x - self.bounds.x_min) / self.dx)
        iy = int((p.y - self.bounds.y_min) / self.dy)
        return ix, iy

    @classmethod
    def default(cls, rink: Rink, dx: float = 1.0, dy: float = 1.0):
        # Seating feature already exists; use its extents
        seating: Seating = rink.feature("seating")       # type: ignore[arg-type]
        aabbs = [s.aabb for s in seating.geometry()]
        shell = AABB.union(aabbs)
        return cls(shell, dx, dy)

    def save_heatmap(self, counts: np.ndarray, filename: str) -> None:
        import matplotlib.pyplot as plt
        plt.imshow(
            counts.T, origin="lower",
            extent=[self.bounds.x_min, self.bounds.x_max,
                    self.bounds.y_min, self.bounds.y_max],
            cmap="inferno")
        plt.colorbar(label="Souvenir probability (hits / shots)")
        plt.title("Predicted souvenir-puck landing density")
        plt.savefig(filename, dpi=250, bbox_inches="tight")
        plt.close()
