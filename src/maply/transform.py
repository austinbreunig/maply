"""Conversion between canvas-pixel coordinates and world coordinates.

The canvas has its origin at the top-left with Y increasing *downwards*. World
coordinates place the origin at the bottom-left with Y increasing *upwards*,
matching the convention shapely geometries are expected to use.
"""

from __future__ import annotations

from dataclasses import dataclass

Coord = tuple[float, float]


@dataclass(frozen=True)
class CanvasTransform:
    """Affine mapping between pixel space and world space.

    A pixel ``(px, py)`` maps to world ``(x, y)`` as::

        x = origin_x + px * scale
        y = origin_y + (height - py) * scale

    With the defaults (``scale=1``, ``origin=(0, 0)``) world coordinates equal
    pixel coordinates with the Y axis flipped so that up is positive.
    """

    height: float
    scale: float = 1.0
    origin_x: float = 0.0
    origin_y: float = 0.0

    def to_world(self, px: float, py: float) -> Coord:
        """Convert a canvas-pixel coordinate to world space."""
        x = self.origin_x + px * self.scale
        y = self.origin_y + (self.height - py) * self.scale
        return (x, y)

    def to_pixel(self, x: float, y: float) -> Coord:
        """Convert a world coordinate back to canvas-pixel space."""
        px = (x - self.origin_x) / self.scale
        py = self.height - (y - self.origin_y) / self.scale
        return (px, py)
