"""Tests for the maply.interaction state machine."""

from maply.interaction import Interaction
from maply.model import DrawState
from maply.tools import Tool


def make(tool: Tool) -> Interaction:
    return Interaction(DrawState(), tool=tool)


def test_point_commits_immediately():
    ix = make(Tool.POINT)
    ix.on_press(5, 5)
    assert len(ix.state.shapes) == 1
    assert ix.state.shapes[0].kind is Tool.POINT
    assert ix.state.draft is None


def test_line_sequence_and_finish():
    ix = make(Tool.LINE)
    ix.on_press(0, 0)
    ix.on_press(1, 1)
    ix.on_press(2, 2)
    assert ix.state.draft is not None
    assert len(ix.state.shapes) == 0
    ix.finish()
    assert len(ix.state.shapes) == 1
    assert ix.state.shapes[0].exterior == [(0, 0), (1, 1), (2, 2)]


def test_polygon_closes_near_start():
    ix = make(Tool.POLYGON)
    ix.on_press(0, 0)
    ix.on_press(100, 0)
    ix.on_press(100, 100)
    # Click back near the first vertex to close.
    ix.on_press(2, 1)
    assert len(ix.state.shapes) == 1
    assert ix.state.draft is None


def test_polygon_does_not_close_when_far():
    ix = make(Tool.POLYGON)
    ix.on_press(0, 0)
    ix.on_press(100, 0)
    ix.on_press(100, 100)
    ix.on_press(50, 50)  # far from start -> just another vertex
    assert ix.state.draft is not None
    assert len(ix.state.draft.exterior) == 4


def test_rectangle_drag():
    ix = make(Tool.RECT)
    ix.on_press(0, 0)
    ix.on_move(10, 5)
    ix.on_release(10, 5)
    assert len(ix.state.shapes) == 1
    rect = ix.state.shapes[0]
    assert rect.exterior == [(0, 0), (10, 0), (10, 5), (0, 5)]


def test_circle_drag_sets_radius():
    ix = make(Tool.CIRCLE)
    ix.on_press(0, 0)
    ix.on_move(3, 4)
    ix.on_release(3, 4)
    assert len(ix.state.shapes) == 1
    circle = ix.state.shapes[0]
    assert circle.center == (0, 0)
    assert circle.radius == 5.0  # 3-4-5 triangle


def test_set_tool_discards_draft():
    ix = make(Tool.LINE)
    ix.on_press(0, 0)
    ix.on_press(1, 1)
    ix.set_tool(Tool.POINT)
    assert ix.state.draft is None
    assert ix.tool is Tool.POINT


def test_undo_vertex_then_shape():
    ix = make(Tool.LINE)
    ix.on_press(0, 0)
    ix.on_press(1, 1)
    ix.undo()  # removes a vertex
    assert len(ix.state.draft.exterior) == 1
    ix.undo()  # removes last vertex -> draft cleared
    assert ix.state.draft is None

    ix.on_press(0, 0)
    ix.on_press(1, 1)
    ix.finish()
    assert len(ix.state.shapes) == 1
    ix.undo()  # no draft -> removes the committed shape
    assert len(ix.state.shapes) == 0


def test_clear():
    ix = make(Tool.POINT)
    ix.on_press(1, 1)
    ix.on_press(2, 2)
    ix.clear()
    assert ix.state.shapes == []
    assert ix.state.draft is None
