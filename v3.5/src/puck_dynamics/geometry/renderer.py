from __future__ import annotations

import abc
from pathlib import Path
from typing import Literal, Optional, Tuple

from puck_dynamics.geometry import (
    Box3D,
    Cylinder,
    Plane3D,
    Polyline2D,
    Arc2D,
)  # type: ignore[attr-defined]

from .colors import (
    Color,
    ICE_BLUE,
    LINE_RED,
    LINE_BLUE,
    GOAL_POST_RED,
    BOARD_YELLOW,
    GLASS_TINT,
)

class BaseRenderer(abc.ABC):

    @abc.abstractmethod
    def draw_feature(self, feature, **kwargs):
        """
        Dispatch drawing based on the feature's internal geometry.

        Implementations should fallback gracefully if they encounter a geometry
        primitive they do not understand (e.g. issue a warning and continue).
        """

    @abc.abstractmethod
    def show(self, *args, **kwargs):
        "Display the rendered scene (blocking or non-blocking)."

    @abc.abstractmethod
    def savefig(self, path: str | Path, dpi: int = 300):
        "Write the current frame to disk."


    def _color_for(self, geom) -> Color:
        """
        Heuristic mapping from geometry object to colour.

        Concrete subclasses may override; default picks commonly used colours.
        """
        if isinstance(geom, Cylinder):
            return GOAL_POST_RED
        if isinstance(geom, Plane3D):
            return ICE_BLUE
        if isinstance(geom, Box3D):
            return BOARD_YELLOW
        return (0.5, 0.5, 0.5, 1.0)  # fallback grey

class MatplotlibRinkRenderer(BaseRenderer):
 

    def __init__(
        self,
        figsize: Tuple[float, float] = (12, 7),
        ice_color: Color = ICE_BLUE,
        line_red: Color = LINE_RED,
        line_blue: Color = LINE_BLUE,
        glass_tint: Color = GLASS_TINT,
        background: Color | Literal["none"] = "none",
    ):
        import matplotlib.pyplot as _plt  # delayed import

        self._plt = _plt
        self._background = background if background != "none" else ICE_BLUE
        self._fig, self._ax = _plt.subplots(figsize=figsize)
        self._ax.set_aspect("equal", adjustable="box")
        self._fig.patch.set_facecolor(self._background)
        self._ax.set_facecolor(self._background)
        self._ax.axis("off")
        self._bounds: Optional[Tuple[float, float, float, float]] = None

        # store palette
        self._palette = dict(
            ice=ice_color,
            red=line_red,
            blue=line_blue,
            board=BOARD_YELLOW,
            glass=glass_tint,
        )

    def draw_feature(self, feature, **kwargs):
        """
        Iterate over feature.geometry() and draw what we recognise.
        """
        feature_name = getattr(feature, "name", None)
        for geom in feature.geometry():
            self._update_bounds(geom)
            if isinstance(geom, Plane3D):
                if feature_name != "rink_surface":
                    self._draw_plane_like(geom, feature_name=feature_name, **kwargs)
            elif isinstance(geom, Box3D):
                self._draw_plane_like(geom, feature_name=feature_name, **kwargs)
            elif isinstance(geom, Cylinder):
                self._draw_cylinder(geom, feature_name=feature_name, **kwargs)
            elif isinstance(geom, (Polyline2D, Arc2D)):
                self._draw_polyline(geom, feature_name=feature_name, **kwargs)
            else:  # pragma: no cover
                # unknown primitive – skip with notice
                import warnings

                warnings.warn(f"Renderer: unsupported geometry {type(geom)}")

    def show(self, block: bool = True):
        self._plt.show(block=block)

    def savefig(self, path: str | Path, dpi: int = 300, transparent: bool | None = None, **kwargs):
        if transparent is None:
            transparent = False
        if self._bounds is not None:
            xmin, xmax, ymin, ymax = self._bounds
            span_x = max(xmax - xmin, 1.0)
            span_y = max(ymax - ymin, 1.0)
            margin_x = span_x * 0.08
            margin_y = span_y * 0.08
            self._ax.set_xlim(xmin - margin_x, xmax + margin_x)
            self._ax.set_ylim(ymin - margin_y, ymax + margin_y)
        else:
            self._ax.set_xlim(-60, 60)
            self._ax.set_ylim(-40, 40)
        self._ax.set_aspect("equal", adjustable="box")
        self._fig.tight_layout(pad=0.2)
        self._fig.savefig(
            path,
            dpi=dpi,
            transparent=transparent,
            facecolor=self._fig.get_facecolor(),
            **kwargs,
        )

    def _update_bounds(self, geom) -> None:
        if isinstance(geom, Box3D):
            xs = [geom.min_pt.x, geom.max_pt.x]
            ys = [geom.min_pt.y, geom.max_pt.y]
        elif isinstance(geom, Plane3D):
            pts = geom.project_to_xy().vertices()
            xs = [p.x for p in pts]
            ys = [p.y for p in pts]
        elif isinstance(geom, (Polyline2D, Arc2D)):
            pts = geom.discretize(128)
            xs = [p.x for p in pts]
            ys = [p.y for p in pts]
        elif isinstance(geom, Cylinder):
            xs = [geom.base_center.x - geom.radius, geom.base_center.x + geom.radius]
            ys = [geom.base_center.y - geom.radius, geom.base_center.y + geom.radius]
        else:
            return

        if self._bounds is None:
            self._bounds = (min(xs), max(xs), min(ys), max(ys))
        else:
            xmin, xmax, ymin, ymax = self._bounds
            self._bounds = (min(xmin, min(xs)), max(xmax, max(xs)), min(ymin, min(ys)), max(ymax, max(ys)))

    def _draw_plane_like(self, geom, feature_name=None, **kwargs):
        if isinstance(geom, Box3D):
            x0, x1 = geom.min_pt.x, geom.max_pt.x
            y0, y1 = geom.min_pt.y, geom.max_pt.y
            vertices = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        else:
            # Extract XY footprint for Plane3D and other shapes with projection
            vertices = [(v.x, v.y) for v in geom.project_to_xy().vertices()]

        color = kwargs.get("color")
        if color is None:
            if feature_name == "rink_surface" and isinstance(geom, Plane3D):
                color = self._palette["ice"]
            else:
                color = self._color_for(geom)

        edgecolor = kwargs.get("edgecolor")
        if edgecolor is None:
            edgecolor = self._palette["red"] if feature_name == "rink_surface" else "none"

        fill = kwargs.get("fill", True)
        alpha = kwargs.get("alpha", None)
        if isinstance(color, tuple) and len(color) == 4:
            if alpha is None:
                alpha = color[3]
            if color[3] < 1.0 and edgecolor == "none":
                edgecolor = (0, 0, 0, 0.35)

        linewidth = kwargs.get("lw", 2.0 if feature_name == "rink_surface" else 0.0)
        poly = self._plt.Polygon(
            vertices,
            closed=True,
            facecolor=color if fill else "none",
            linewidth=linewidth,
            edgecolor=edgecolor,
            alpha=alpha,
            zorder=1,
        )
        self._ax.add_patch(poly)

    def _draw_cylinder(self, cyl: Cylinder, **kwargs):
        # Only render small vertical cylinders as top-down circles.
        # Horizontal or slanted cylinders are 3D constructs (crossbars, netting)
        # and should not be projected as simple top-down discs.
        axis = cyl.axis
        if hasattr(axis, "z") and abs(axis.z) < 0.9:
            return
        if cyl.radius > 1.0 or cyl.height > 3.0:
            return

        facecolor = kwargs.get("color", self._color_for(cyl))
        edgecolor = kwargs.get("edgecolor")
        if edgecolor is None:
            edgecolor = (0.0, 0.0, 0.0, 0.15) if kwargs.get("color") is None else "none"
        alpha = kwargs.get("alpha", None)
        if isinstance(facecolor, tuple) and len(facecolor) == 4 and alpha is None:
            alpha = facecolor[3]
        circle = self._plt.Circle(
            (cyl.base_center.x, cyl.base_center.y),
            radius=cyl.radius,
            facecolor=facecolor,
            edgecolor=edgecolor,
            fill=kwargs.get("fill", True),
            linewidth=kwargs.get("lw", 1.2),
            alpha=alpha,
            zorder=2,
        )
        self._ax.add_patch(circle)

    def _draw_polyline(self, line, feature_name=None, **kwargs):
        pts = line.discretize(128)
        xs, ys = zip(*[(p.x, p.y) for p in pts])
        color = kwargs.get("color")
        if color is None:
            if feature_name == "rink_surface":
                color = self._palette["red"]
            elif feature_name == "boards":
                color = self._palette["board"]
            else:
                color = self._color_for(line)

        alpha = kwargs.get("alpha", None)
        if isinstance(color, tuple) and len(color) == 4 and alpha is None:
            alpha = color[3]

        if isinstance(line, Polyline2D):
            if feature_name == "rink_surface":
                # Fill the official rink outline with rounded corners.
                polygon = self._plt.Polygon(
                    list(zip(xs, ys)),
                    closed=True,
                    facecolor=kwargs.get("fill_color", kwargs.get("color", self._palette["ice"])),
                    edgecolor=color,
                    linewidth=kwargs.get("lw", 2.5),
                    alpha=alpha,
                    zorder=1,
                )
                self._ax.add_patch(polygon)
                return

            if kwargs.get("fill", False):
                polygon = self._plt.Polygon(
                    list(zip(xs, ys)),
                    closed=True,
                    facecolor=kwargs.get("fill_color", kwargs.get("color", color)),
                    edgecolor=kwargs.get("edgecolor", color),
                    linewidth=kwargs.get("lw", 2.5),
                    alpha=alpha,
                    zorder=2,
                )
                self._ax.add_patch(polygon)
                return

        self._ax.plot(
            xs,
            ys,
            color=color,
            linewidth=kwargs.get("lw", 2.5),
            alpha=alpha,
            solid_capstyle="round",
            solid_joinstyle="round",
            zorder=3,
        )


Renderer = MatplotlibRinkRenderer
