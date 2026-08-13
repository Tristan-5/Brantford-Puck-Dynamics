from __future__ import annotations
import numpy as np
from puck_dynamics.geometry import AABB, Point3D as Vec
from puck_dynamics.arena import Rink
from puck_dynamics.arena.dimensions import NHLStandardDimensions
from puck_dynamics.arena.features.seating import Seating

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

    @classmethod
    def outside_rink(cls,
                     rink: Rink,
                     dx: float = 1.0,
                     dy: float = 1.0,
                     margin: float = 40.0) -> "SeatingGrid":
        """Create a grid covering the rink and a wide margin around it.

        The bounds are expressed in the centered rink coordinate system, which
        matches the simulation's world frame.
        """
        dims = getattr(rink, "dims", NHLStandardDimensions())
        half_len = dims.length / 2.0
        half_wid = dims.width / 2.0
        bounds = AABB.from_bounds(
            x_min=-half_len - margin,
            x_max=+half_len + margin,
            y_min=-half_wid - margin,
            y_max=+half_wid + margin,
            z_min=0.0,
            z_max=0.0,
        )
        return cls(bounds, dx, dy)

    def rink_overlay_bounds(self) -> tuple[float, float, float, float]:
        dims = NHLStandardDimensions()
        return (-dims.length / 2.0, dims.length / 2.0,
                -dims.width / 2.0, dims.width / 2.0)

    def _point_is_inside_rink(self, x: float, y: float) -> bool:
        dims = NHLStandardDimensions()
        half_len = dims.length / 2.0
        half_wid = dims.width / 2.0
        corner_r = dims.corner_radius

        if abs(x) <= half_len - corner_r and abs(y) <= half_wid - corner_r:
            return True

        corners = [
            (half_len - corner_r, half_wid - corner_r),
            (half_len - corner_r, -half_wid + corner_r),
            (-half_len + corner_r, -half_wid + corner_r),
            (-half_len + corner_r, half_wid - corner_r),
        ]
        for cx, cy in corners:
            if (x - cx) ** 2 + (y - cy) ** 2 <= corner_r ** 2:
                return True
        return False

    @staticmethod
    def _gaussian_kernel1d(sigma_cells: float) -> np.ndarray:
        if sigma_cells <= 0.0:
            return np.array([1.0], dtype=np.float64)
        radius = max(1, int(np.ceil(3.0 * sigma_cells)))
        x = np.arange(-radius, radius + 1, dtype=np.float64)
        k = np.exp(-0.5 * (x / sigma_cells) ** 2)
        k /= k.sum()
        return k

    @staticmethod
    def _convolve_along_axis(arr: np.ndarray, kernel: np.ndarray, axis: int) -> np.ndarray:
        return np.apply_along_axis(lambda v: np.convolve(v, kernel, mode="same"), axis, arr)

    def smooth_probabilities(self, probs: np.ndarray, sigma_m: float = 1.25) -> np.ndarray:
        sigma_x = max(0.0, sigma_m / max(self.dx, 1e-9))
        sigma_y = max(0.0, sigma_m / max(self.dy, 1e-9))
        kx = self._gaussian_kernel1d(sigma_x)
        ky = self._gaussian_kernel1d(sigma_y)

        valid = np.ones_like(probs, dtype=np.float64)
        for ix in range(valid.shape[0]):
            x = self.bounds.x_min + (ix + 0.5) * self.dx
            for iy in range(valid.shape[1]):
                y = self.bounds.y_min + (iy + 0.5) * self.dy
                if self._point_is_inside_rink(x, y):
                    valid[ix, iy] = 0.0

        weighted = probs.astype(np.float64, copy=False) * valid
        num = self._convolve_along_axis(weighted, kx, axis=0)
        num = self._convolve_along_axis(num, ky, axis=1)
        den = self._convolve_along_axis(valid, kx, axis=0)
        den = self._convolve_along_axis(den, ky, axis=1)

        smoothed = np.divide(num, den, out=np.zeros_like(num), where=den > 1e-12)
        total = smoothed.sum()
        if total > 0:
            smoothed /= total
        return smoothed

    def debias_symmetry(self, probs: np.ndarray, blend: float = 0.6) -> np.ndarray:
        """Blend with mirrored fields to reduce Monte Carlo directional bias.

        blend=0 keeps raw probs, blend=1 uses fully symmetrized probs.
        """
        b = float(min(1.0, max(0.0, blend)))
        sym = (
            probs
            + np.flip(probs, axis=0)
            + np.flip(probs, axis=1)
            + np.flip(np.flip(probs, axis=0), axis=1)
        ) / 4.0
        out = (1.0 - b) * probs + b * sym
        total = out.sum()
        if total > 0:
            out = out / total
        return out

    def save_heatmap(self, counts: np.ndarray, filename: str) -> None:
        import matplotlib.pyplot as plt
        from matplotlib.colors import PowerNorm
        from matplotlib.patches import Polygon

        fig, ax = plt.subplots()

        plotted = self.smooth_probabilities(counts, sigma_m=1.25)
        outside_mask = np.ones_like(plotted, dtype=bool)
        for ix in range(plotted.shape[0]):
            x = self.bounds.x_min + (ix + 0.5) * self.dx
            for iy in range(plotted.shape[1]):
                y = self.bounds.y_min + (iy + 0.5) * self.dy
                if self._point_is_inside_rink(x, y):
                    plotted[ix, iy] = np.nan
                    outside_mask[ix, iy] = False

        # Visualization floor: keep tiny nonzero colour across all outside bins
        # so the field reads as a continuous probability surface.
        if np.any(outside_mask):
            finite = plotted[outside_mask]
            peak = float(np.nanmax(finite)) if finite.size else 0.0
            floor = max(peak * 0.012, 1e-12)
            plotted[outside_mask] = plotted[outside_mask] + floor
            norm_total = np.nansum(plotted[outside_mask])
            if norm_total > 0:
                plotted[outside_mask] = plotted[outside_mask] / norm_total

        cmap = plt.get_cmap("inferno").copy()
        cmap.set_bad("white", alpha=1.0)

        ax.imshow(
            plotted.T,
            origin="lower",
            extent=[self.bounds.x_min, self.bounds.x_max,
                    self.bounds.y_min, self.bounds.y_max],
            cmap=cmap,
            interpolation="nearest",
            norm=PowerNorm(gamma=0.55, vmin=0.0),
        )

        outline = None
        try:
            from puck_dynamics.tools.render_rink_trimesh import make_rink_outline

            outline_poly = make_rink_outline(NHLStandardDimensions())
            outline = list(outline_poly.exterior.coords)
        except Exception:
            rink = Rink()
            for geom in rink.feature("rink_surface").geometry():
                discretize = getattr(geom, "discretize", None)
                if discretize is None:
                    continue
                points = discretize(256)
                outline = [(point.x, point.y) for point in points]
                break

        if outline is None:
            x0, x1, y0, y1 = self.rink_overlay_bounds()
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

        fig.colorbar(ax.images[0], ax=ax, label="Souvenir probability (hits / shots)")
        ax.set_title("Predicted souvenir-puck landing density")
        fig.savefig(filename, dpi=250)
        plt.close(fig)

    def save_outside_rink_heatmap(self, counts: np.ndarray, filename: str) -> None:
        self.save_heatmap(counts, filename)
