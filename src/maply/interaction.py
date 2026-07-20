"""Pointer interaction state machine.

This module translates raw pointer gestures (in **world** coordinates) into
mutations on a :class:`~maply.model.DrawState`. It is deliberately free of any
``ipycanvas`` / ``ipywidgets`` dependency so it can be driven directly from
unit tests.

Interaction model per tool:

- ``POINT``   : each press commits a single-point shape.
- ``LINE``    : each press appends a vertex; :meth:`Interaction.finish` commits.
- ``POLYGON`` : each press appends a vertex; pressing near the first vertex, or
  calling :meth:`Interaction.finish`, closes and commits the ring.
- ``RECT``    : press sets one corner, release sets the opposite corner.
- ``CIRCLE``  : press sets the center, release sets the radius.
"""

from __future__ import annotations

import math

from maply.model import DrawState, Shape
from maply.tools import Tool

Coord = tuple[float, float]

# Pointer must be within this many world units of the first polygon vertex to
# close the ring by clicking.
CLOSE_TOLERANCE = 10.0


def _distance(a: Coord, b: Coord) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _rect_ring(a: Coord, b: Coord) -> list[Coord]:
    """Return the 4-corner ring of the axis-aligned rectangle spanning a..b."""
    (x0, y0), (x1, y1) = a, b
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


class Interaction:
    """Drives a :class:`DrawState` in response to pointer gestures.

    All coordinates passed in are expected to be **world** coordinates.
    """

    def __init__(
        self,
        state: DrawState,
        tool: Tool = Tool.POLYGON,
        close_tolerance: float = CLOSE_TOLERANCE,
    ):
        self.state = state
        self.tool = tool
        self.close_tolerance = close_tolerance
        self._drag_start: Coord | None = None

    def set_tool(self, tool: Tool) -> None:
        """Switch the active tool, discarding any in-progress draft."""
        self.state.draft = None
        self._drag_start = None
        self.tool = tool

    # -- pointer events ---------------------------------------------------

    def on_press(self, x: float, y: float) -> None:
        """Handle a pointer press at world coordinate ``(x, y)``."""
        point = (x, y)
        if self.tool is Tool.POINT:
            self.state.draft = Shape(kind=Tool.POINT, exterior=[point])
            self.state.commit_draft()
            return

        if self.tool.is_drag:
            self._drag_start = point
            kind = self.tool
            if kind is Tool.RECT:
                self.state.draft = Shape(kind=Tool.RECT, exterior=_rect_ring(point, point))
            else:  # CIRCLE
                self.state.draft = Shape(kind=Tool.CIRCLE, center=point, radius=0.0)
            return

        # Click-sequence tools: LINE / POLYGON.
        draft = self.state.draft
        if draft is None:
            self.state.draft = Shape(kind=self.tool, exterior=[point])
            return

        # Close the polygon if the user clicks near the starting vertex.
        if (
            self.tool is Tool.POLYGON
            and len(draft.exterior) >= 3
            and _distance(point, draft.exterior[0]) <= self.close_tolerance
        ):
            self.finish()
            return

        draft.exterior.append(point)

    def on_move(self, x: float, y: float) -> None:
        """Handle pointer movement; updates preview state only."""
        point = (x, y)
        self.state.cursor = point
        if self._drag_start is None or self.state.draft is None:
            return
        if self.tool is Tool.RECT:
            self.state.draft.exterior = _rect_ring(self._drag_start, point)
        elif self.tool is Tool.CIRCLE:
            self.state.draft.radius = _distance(self._drag_start, point)

    def on_release(self, x: float, y: float) -> None:
        """Handle a pointer release; commits drag-based shapes."""
        if self._drag_start is None:
            return
        self.on_move(x, y)
        self._drag_start = None
        self.state.commit_draft()

    # -- explicit actions -------------------------------------------------

    def finish(self) -> Shape | None:
        """Commit the current click-sequence draft (line / polygon)."""
        return self.state.commit_draft()

    def cancel(self) -> None:
        """Discard the current draft without committing it."""
        self.state.draft = None
        self._drag_start = None

    def undo(self) -> None:
        """Undo the last vertex if drafting, otherwise the last shape."""
        if self.state.draft is not None:
            self.state.undo_last_vertex()
        else:
            self.state.undo_last_shape()

    def clear(self) -> None:
        """Remove everything."""
        self._drag_start = None
        self.state.clear()
