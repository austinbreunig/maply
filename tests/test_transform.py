"""Tests for maply.transform."""

from maply.transform import CanvasTransform


def test_identity_scale_flips_y():
    t = CanvasTransform(height=400)
    # Top-left pixel (0, 0) maps to world (0, 400) with Y flipped up.
    assert t.to_world(0, 0) == (0.0, 400.0)
    # Bottom-left pixel (0, 400) maps to world origin.
    assert t.to_world(0, 400) == (0.0, 0.0)


def test_round_trip_pixel_world():
    t = CanvasTransform(height=300, scale=2.0, origin_x=10.0, origin_y=-5.0)
    for px, py in [(0, 0), (50, 120), (299, 300)]:
        x, y = t.to_world(px, py)
        back = t.to_pixel(x, y)
        assert back[0] == px
        assert back[1] == py


def test_scale_applied():
    t = CanvasTransform(height=100, scale=3.0)
    assert t.to_world(2, 100) == (6.0, 0.0)
