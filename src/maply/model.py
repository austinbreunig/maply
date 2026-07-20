"""Data model for drawn shapes.

Coordinates stored on :class:`Shape` are in **world** space (Y-up, arbitrary
units) — the canvas-pixel-to-world conversion happens in
:mod:`maply.transform` before a shape is committed to the model.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from maply.tools import Tool

Coord = tuple[float, float]
Ring = list[Coord]


@dataclass
class Shape:
    """A single drawn geometry in world coordinates.

    The interpretation of the stored data depends on ``kind``:

    - ``POINT``   : ``exterior`` holds exactly one coordinate.
    - ``LINE``    : ``exterior`` holds the ordered vertices of the line.
    - ``POLYGON`` : ``exterior`` is the outer ring; ``holes`` are interior rings.
    - ``RECT``    : ``exterior`` holds the 4 corners (stored as a polygon ring).
    - ``CIRCLE``  : ``center`` and ``radius`` are set; ``exterior`` is ignored.
    """

    kind: Tool
    exterior: Ring = field(default_factory=list)
    holes: list[Ring] = field(default_factory=list)
    center: Coord | None = None
    radius: float | None = None

    def is_valid(self) -> bool:
        """Return whether the shape has enough vertices to form its geometry."""
        if self.kind is Tool.POINT:
            return len(self.exterior) == 1
        if self.kind is Tool.LINE:
            return len(self.exterior) >= 2
        if self.kind in (Tool.POLYGON, Tool.RECT):
            return len(self.exterior) >= 3
        if self.kind is Tool.CIRCLE:
            return self.center is not None and (self.radius or 0) > 0
        return False


@dataclass
class DrawState:
    """Mutable drawing state shared between interaction, rendering and export.

    ``shapes`` holds completed shapes. ``draft`` is the shape currently being
    drawn (if any), and ``cursor`` is the last-known pointer position in world
    coordinates, used to preview the in-progress segment.
    """

    shapes: list[Shape] = field(default_factory=list)
    draft: Shape | None = None
    cursor: Coord | None = None

    def commit_draft(self) -> Shape | None:
        """Move the current draft into ``shapes`` if it is valid.

        Returns the committed shape, or ``None`` if there was no valid draft.
        """
        if self.draft is not None and self.draft.is_valid():
            shape = self.draft
            self.shapes.append(shape)
            self.draft = None
            return shape
        self.draft = None
        return None

    def undo_last_vertex(self) -> None:
        """Remove the most recently added vertex from the active draft."""
        if self.draft is not None and self.draft.exterior:
            self.draft.exterior.pop()
            if not self.draft.exterior:
                self.draft = None

    def undo_last_shape(self) -> Shape | None:
        """Remove and return the most recently completed shape."""
        if self.shapes:
            return self.shapes.pop()
        return None

    def clear(self) -> None:
        """Remove all shapes and any in-progress draft."""
        self.shapes.clear()
        self.draft = None
        self.cursor = None
