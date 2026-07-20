"""Tests for maply.geometry conversions."""

import math

import pytest
from shapely.geometry import GeometryCollection, LineString, Point, Polygon
from shapely.wkt import loads as wkt_loads

from maply.geometry import (
    circle_to_polygon,
    shape_to_geometry,
    to_collection,
    to_geojson,
    to_shapely,
    to_wkt,
)
from maply.model import Shape
from maply.tools import Tool


def test_point_geometry():
    shape = Shape(kind=Tool.POINT, exterior=[(3.0, 4.0)])
    geom = shape_to_geometry(shape)
    assert isinstance(geom, Point)
    assert (geom.x, geom.y) == (3.0, 4.0)


def test_line_geometry():
    shape = Shape(kind=Tool.LINE, exterior=[(0, 0), (1, 1), (2, 0)])
    geom = shape_to_geometry(shape)
    assert isinstance(geom, LineString)
    assert list(geom.coords) == [(0, 0), (1, 1), (2, 0)]


def test_polygon_with_holes():
    exterior = [(0, 0), (10, 0), (10, 10), (0, 10)]
    hole = [(3, 3), (6, 3), (6, 6), (3, 6)]
    shape = Shape(kind=Tool.POLYGON, exterior=exterior, holes=[hole])
    geom = shape_to_geometry(shape)
    assert isinstance(geom, Polygon)
    assert len(list(geom.interiors)) == 1
    # exterior area 100 minus hole area 9.
    assert geom.area == pytest.approx(91.0)


def test_rectangle_is_polygon():
    shape = Shape(kind=Tool.RECT, exterior=[(0, 0), (4, 0), (4, 2), (0, 2)])
    geom = shape_to_geometry(shape)
    assert isinstance(geom, Polygon)
    assert geom.area == pytest.approx(8.0)


def test_circle_to_polygon_area():
    poly = circle_to_polygon((0, 0), 10, segments=512)
    assert poly.area == pytest.approx(math.pi * 100, rel=1e-3)


def test_circle_shape_geometry():
    shape = Shape(kind=Tool.CIRCLE, center=(5, 5), radius=2.0)
    geom = shape_to_geometry(shape)
    assert isinstance(geom, Polygon)
    assert geom.centroid.x == pytest.approx(5.0)


def test_invalid_shape_raises():
    with pytest.raises(ValueError):
        shape_to_geometry(Shape(kind=Tool.POLYGON, exterior=[(0, 0), (1, 1)]))


def test_to_shapely_skips_invalid():
    shapes = [
        Shape(kind=Tool.POINT, exterior=[(1, 1)]),
        Shape(kind=Tool.POLYGON, exterior=[(0, 0)]),  # invalid, skipped
    ]
    geoms = to_shapely(shapes)
    assert len(geoms) == 1


def test_wkt_round_trips():
    shape = Shape(kind=Tool.POLYGON, exterior=[(0, 0), (2, 0), (2, 2), (0, 2)])
    (wkt,) = to_wkt([shape])
    assert wkt_loads(wkt).equals(shape_to_geometry(shape))


def test_to_collection():
    shapes = [
        Shape(kind=Tool.POINT, exterior=[(1, 1)]),
        Shape(kind=Tool.LINE, exterior=[(0, 0), (1, 1)]),
    ]
    coll = to_collection(shapes)
    assert isinstance(coll, GeometryCollection)
    assert len(coll.geoms) == 2


def test_geojson_structure():
    shapes = [Shape(kind=Tool.POINT, exterior=[(1, 2)])]
    gj = to_geojson(shapes)
    assert gj["type"] == "FeatureCollection"
    assert gj["features"][0]["properties"]["kind"] == "point"
    assert gj["features"][0]["geometry"]["type"] == "Point"
