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
        self._fig, self._ax = _plt.subplots(figsize=figsize)
        self._ax.set_aspect("equal", adjustable="box")
        self._ax.set_facecolor(background if background != "none" else (0, 0, 0, 0))
        self._ax.axis("off")

        # store palette
        self._palette = dict(
            ice=ice_color,
            red=line_red,
            blue=line_blue,
            glass=glass_tint,
        )

    def draw_feature(self, feature, **kwargs):
        """
        Iterate over feature.geometry() and draw what we recognise.
        """
        for geom in feature.geometry():
            if isinstance(geom, (Plane3D, Box3D)):
                self._draw_plane_like(geom, **kwargs)
            elif isinstance(geom, Cylinder):
                self._draw_cylinder(geom, **kwargs)
            elif isinstance(geom, (Polyline2D, Arc2D)):
                self._draw_polyline(geom, **kwargs)
            else:  # pragma: no cover
                # unknown primitive – skip with notice
                import warnings

                warnings.warn(f"Renderer: unsupported geometry {type(geom)}")

    def show(self, block: bool = True):
        self._plt.show(block=block)

    def savefig(self, path: str | Path, dpi: int = 300):
        self._fig.savefig(path, dpi=dpi, transparent=True)

    def _draw_plane_like(self, geom, **kwargs):

        # Extract XY footprint
        xs, ys = zip(*[(v.x, v.y) for v in geom.project_to_xy().vertices()])
        poly = self._plt.Polygon(
            list(zip(xs, ys)),
            closed=True,
            color=kwargs.get("color", self._color_for(geom)),
            linewidth=0,
        )
        self._ax.add_patch(poly)

    def _draw_cylinder(self, cyl: Cylinder, **kwargs):
 
        circle = self._plt.Circle(
            (cyl.base_center.x, cyl.base_center.y),
            radius=cyl.radius,
            color=kwargs.get("color", self._color_for(cyl)),
            fill=kwargs.get("fill", True),
            linewidth=kwargs.get("lw", 1.0),
        )
        self._ax.add_patch(circle)

    def _draw_polyline(self, line, **kwargs):
        xs, ys = zip(*[(p.x, p.y) for p in line.discretize(128)])
        self._ax.plot(
            xs,
            ys,
            color=kwargs.get("color", self._color_for(line)),
            linewidth=kwargs.get("lw", 2.0),
        )
