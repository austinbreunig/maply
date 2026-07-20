"""Drawing tools supported by maply."""

from __future__ import annotations

from enum import Enum


class Tool(str, Enum):
    """The active drawing tool.

    Values are lowercase strings so they can be used directly as
    ``ipywidgets`` toggle-button values.
    """

    POINT = "point"
    LINE = "line"
    POLYGON = "polygon"
    RECT = "rectangle"
    CIRCLE = "circle"

    @property
    def label(self) -> str:
        """Human-friendly label for toolbar buttons."""
        return {
            Tool.POINT: "Point",
            Tool.LINE: "Line",
            Tool.POLYGON: "Polygon",
            Tool.RECT: "Rectangle",
            Tool.CIRCLE: "Circle",
        }[self]

    @property
    def is_drag(self) -> bool:
        """Whether the tool is completed by a press-drag-release gesture."""
        return self in (Tool.RECT, Tool.CIRCLE)

    @property
    def is_click_sequence(self) -> bool:
        """Whether the tool is built from a sequence of clicked vertices."""
        return self in (Tool.LINE, Tool.POLYGON)
