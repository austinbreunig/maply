"""Render :class:`~maply.model.DrawState` onto an ipycanvas ``Canvas``.

Rendering reads world coordinates from the state and converts them back to
pixel space via a :class:`~maply.transform.CanvasTransform` before drawing.
All drawing for a frame is wrapped in ``hold_canvas`` to avoid flicker and to
minimise the number of messages sent to the front end.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ipycanvas import hold_canvas

from maply.model import DrawState, Shape
from maply.tools import Tool
from maply.transform import CanvasTransform

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ipycanvas import Canvas


class RenderStyle:
    """Visual styling constants for the canvas."""

    background = "#ffffff"
    grid = "#eef1f4"
    shape_stroke = "#1f77b4"
    shape_fill = "rgba(31, 119, 180, 0.15)"
    draft_stroke = "#ff7f0e"
    draft_fill = "rgba(255, 127, 14, 0.12)"
    vertex = "#d62728"
    vertex_radius = 3.0
    line_width = 2.0
    grid_step = 50.0


def _draw_ring(canvas: Canvas, points: list[tuple[float, float]], *, close: bool) -> None:
    if not points:
        return
    canvas.begin_path()
    x0, y0 = points[0]
    canvas.move_to(x0, y0)
    for x, y in points[1:]:
        canvas.line_to(x, y)
    if close:
        canvas.close_path()


def _pixel_ring(
    transform: CanvasTransform, ring: list[tuple[float, float]]
) -> list[tuple[float, float]]:
    return [transform.to_pixel(x, y) for x, y in ring]


def draw(
    canvas: Canvas,
    state: DrawState,
    transform: CanvasTransform,
    style: RenderStyle | None = None,
) -> None:
    """Draw the full scene (grid, committed shapes, active draft) onto canvas."""
    style = style or RenderStyle()
    with hold_canvas(canvas):
        canvas.clear()
        _draw_background(canvas, style)
        for shape in state.shapes:
            _draw_shape(canvas, shape, transform, style, draft=False)
        if state.draft is not None:
            _draw_shape(canvas, state.draft, transform, style, draft=True)


def _draw_background(canvas: Canvas, style: RenderStyle) -> None:
    canvas.fill_style = style.background
    canvas.fill_rect(0, 0, canvas.width, canvas.height)

    canvas.stroke_style = style.grid
    canvas.line_width = 1.0
    step = style.grid_step
    x = step
    while x < canvas.width:
        canvas.stroke_line(x, 0, x, canvas.height)
        x += step
    y = step
    while y < canvas.height:
        canvas.stroke_line(0, y, canvas.width, y)
        y += step


def _draw_shape(
    canvas: Canvas,
    shape: Shape,
    transform: CanvasTransform,
    style: RenderStyle,
    *,
    draft: bool,
) -> None:
    stroke = style.draft_stroke if draft else style.shape_stroke
    fill = style.draft_fill if draft else style.shape_fill
    canvas.line_width = style.line_width
    canvas.stroke_style = stroke
    canvas.fill_style = fill

    if shape.kind is Tool.POINT:
        pts = _pixel_ring(transform, shape.exterior)
        _draw_vertices(canvas, pts, style)
        return

    if shape.kind is Tool.CIRCLE and shape.center is not None:
        cx, cy = transform.to_pixel(*shape.center)
        # radius is in world units; scale is uniform so divide by scale.
        r = (shape.radius or 0.0) / transform.scale
        if r > 0:
            canvas.fill_arc(cx, cy, r, 0, 2 * math.pi)
            canvas.stroke_arc(cx, cy, r, 0, 2 * math.pi)
        _draw_vertices(canvas, [(cx, cy)], style)
        return

    pts = _pixel_ring(transform, shape.exterior)
    closed = shape.kind in (Tool.POLYGON, Tool.RECT)
    if closed and len(pts) >= 3:
        _draw_ring(canvas, pts, close=True)
        canvas.fill()
        canvas.stroke()
        for hole in shape.holes:
            _draw_ring(canvas, _pixel_ring(transform, hole), close=True)
            canvas.stroke()
    else:
        _draw_ring(canvas, pts, close=False)
        canvas.stroke()
    _draw_vertices(canvas, pts, style)


def _draw_vertices(canvas: Canvas, pixels: list[tuple[float, float]], style: RenderStyle) -> None:
    canvas.fill_style = style.vertex
    for px, py in pixels:
        canvas.fill_arc(px, py, style.vertex_radius, 0, 2 * math.pi)
