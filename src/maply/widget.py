"""The :class:`MaplyCanvas` widget — the public entry point of maply.

It composes an ``ipycanvas`` drawing surface with an ``ipywidgets`` toolbar and
wires pointer events into the :class:`~maply.interaction.Interaction` state
machine. Drawn shapes are exposed as shapely geometries, WKT, GeoJSON, or a
GeoDataFrame.
"""

from __future__ import annotations

from typing import Any

import ipywidgets as widgets
from ipycanvas import Canvas

from maply import geometry, render
from maply.interaction import Interaction
from maply.model import DrawState
from maply.tools import Tool
from maply.transform import CanvasTransform


class MaplyCanvas(widgets.VBox):
    """Interactive shape-drawing widget.

    Parameters
    ----------
    width, height:
        Canvas size in pixels.
    scale:
        World units per pixel. With ``scale=1`` world coordinates equal pixel
        coordinates (Y flipped so up is positive).
    origin:
        World coordinate of the canvas bottom-left corner.
    tool:
        The tool selected on start-up.
    """

    def __init__(
        self,
        width: int = 600,
        height: int = 400,
        *,
        scale: float = 1.0,
        origin: tuple[float, float] = (0.0, 0.0),
        tool: Tool = Tool.POLYGON,
    ):
        self.state = DrawState()
        self.transform = CanvasTransform(
            height=height, scale=scale, origin_x=origin[0], origin_y=origin[1]
        )
        self.interaction = Interaction(self.state, tool=tool)

        self.canvas = Canvas(width=width, height=height)
        self.canvas.on_mouse_down(self._on_mouse_down)
        self.canvas.on_mouse_move(self._on_mouse_move)
        self.canvas.on_mouse_up(self._on_mouse_up)

        toolbar = self._build_toolbar(tool)
        super().__init__([toolbar, self.canvas])
        self._redraw()

    # -- toolbar ----------------------------------------------------------

    def _build_toolbar(self, tool: Tool) -> widgets.Widget:
        self._tool_buttons = widgets.ToggleButtons(
            options=[(t.label, t) for t in Tool],
            value=tool,
            description="Tool:",
        )
        self._tool_buttons.observe(self._on_tool_change, names="value")

        finish_btn = widgets.Button(
            description="Finish", tooltip="Complete the current line/polygon"
        )
        undo_btn = widgets.Button(
            description="Undo", tooltip="Remove the last vertex or shape"
        )
        clear_btn = widgets.Button(description="Clear", tooltip="Remove all shapes")
        finish_btn.on_click(lambda _: self._finish())
        undo_btn.on_click(lambda _: self._undo())
        clear_btn.on_click(lambda _: self._clear())

        actions = widgets.HBox([finish_btn, undo_btn, clear_btn])
        return widgets.VBox([self._tool_buttons, actions])

    # -- event handlers ---------------------------------------------------

    def _on_tool_change(self, change: dict[str, Any]) -> None:
        self.interaction.set_tool(change["new"])
        self._redraw()

    def _on_mouse_down(self, px: float, py: float) -> None:
        x, y = self.transform.to_world(px, py)
        self.interaction.on_press(x, y)
        self._redraw()

    def _on_mouse_move(self, px: float, py: float) -> None:
        x, y = self.transform.to_world(px, py)
        self.interaction.on_move(x, y)
        # Only redraw while there is something to preview.
        if self.state.draft is not None:
            self._redraw()

    def _on_mouse_up(self, px: float, py: float) -> None:
        x, y = self.transform.to_world(px, py)
        self.interaction.on_release(x, y)
        self._redraw()

    def _finish(self) -> None:
        self.interaction.finish()
        self._redraw()

    def _undo(self) -> None:
        self.interaction.undo()
        self._redraw()

    def _clear(self) -> None:
        self.interaction.clear()
        self._redraw()

    def _redraw(self) -> None:
        render.draw(self.canvas, self.state, self.transform)

    # -- public API -------------------------------------------------------

    @property
    def shapes(self):
        """The list of committed :class:`~maply.model.Shape` objects."""
        return self.state.shapes

    @property
    def geometries(self):
        """All drawn shapes as shapely geometries."""
        return geometry.to_shapely(self.state.shapes)

    @property
    def wkt(self) -> list[str]:
        """WKT strings for all drawn shapes."""
        return geometry.to_wkt(self.state.shapes)

    @property
    def geojson(self) -> dict[str, Any]:
        """A GeoJSON ``FeatureCollection`` of all drawn shapes."""
        return geometry.to_geojson(self.state.shapes)

    def to_collection(self):
        """Bundle all drawn shapes into a shapely ``GeometryCollection``."""
        return geometry.to_collection(self.state.shapes)

    def to_geodataframe(self):
        """Return a geopandas ``GeoDataFrame`` (requires the geopandas extra)."""
        return geometry.to_geodataframe(self.state.shapes)

    def clear(self) -> None:
        """Programmatically remove all shapes."""
        self._clear()
