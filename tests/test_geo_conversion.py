"""Tests for the geographic conversion helpers in maply.geometry.

These cover the pure-Python glue between GeoJSON (as produced by ipyleaflet's
draw control) and shapely — no map or kernel required.
"""

import math

import pytest
from shapely.geometry import LineString, Point, Polygon
from shapely.geometry import mapping as shapely_mapping
from shapely.wkt import loads as wkt_loads

from maply.geometry import (
    features_to_geometries,
    geographic_circle,
    geojson_feature_to_geometry,
    geometries_to_collection,
    geometries_to_geojson,
    geometries_to_wkt,
)


def _feature(geom, **props):
    return {"type": "Feature", "properties": props, "geometry": shapely_mapping(geom)}


def test_geojson_polygon_feature():
    poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    geom = geojson_feature_to_geometry(_feature(poly))
    assert isinstance(geom, Polygon)
    assert geom.equals(poly)


def test_geojson_point_and_line():
    assert isinstance(geojson_feature_to_geometry(_feature(Point(1, 2))), Point)
    line = LineString([(0, 0), (2, 2)])
    assert isinstance(geojson_feature_to_geometry(_feature(line)), LineString)


def test_geojson_bare_geometry_accepted():
    # A raw geometry mapping (no Feature wrapper) should also work.
    geom = geojson_feature_to_geometry(shapely_mapping(Point(3, 4)))
    assert isinstance(geom, Point)


def test_circle_feature_point_with_radius_is_polygonised():
    # Leaflet/Geoman convention: a circle is a Point carrying a metre radius.
    feature = {
        "type": "Feature",
        "properties": {"radius": 1000.0},
        "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
    }
    geom = geojson_feature_to_geometry(feature)
    assert isinstance(geom, Polygon)
    # ~1 km radius near the equator -> ~0.009 deg; centroid stays at origin.
    assert geom.centroid.x == pytest.approx(0.0, abs=1e-6)
    assert geom.centroid.y == pytest.approx(0.0, abs=1e-6)


def test_geographic_circle_radius_scales_with_latitude():
    # Longitude span grows with latitude (cos correction); latitude span does not.
    equator = geographic_circle((0.0, 0.0), 1000.0)
    high = geographic_circle((0.0, 60.0), 1000.0)
    assert equator.bounds[2] - equator.bounds[0] < high.bounds[2] - high.bounds[0]


def test_geographic_circle_rejects_nonpositive():
    with pytest.raises(ValueError):
        geographic_circle((0, 0), 0.0)


def test_features_to_geometries_roundtrip():
    geoms = [Point(0, 0), LineString([(0, 0), (1, 1)])]
    features = [_feature(g) for g in geoms]
    back = features_to_geometries(features)
    assert [type(g) for g in back] == [Point, LineString]


def test_geometries_to_wkt_round_trips():
    poly = Polygon([(0, 0), (2, 0), (2, 2), (0, 2)])
    (wkt,) = geometries_to_wkt([poly])
    assert wkt_loads(wkt).equals(poly)


def test_geometries_to_collection():
    coll = geometries_to_collection([Point(0, 0), Point(1, 1)])
    assert len(coll.geoms) == 2


def test_geometries_to_geojson_kinds_and_crs():
    gj = geometries_to_geojson([Point(0, 0)], kinds=["marker"], crs="EPSG:4326")
    assert gj["type"] == "FeatureCollection"
    assert gj["features"][0]["properties"]["kind"] == "marker"
    # WGS84 must not add a crs member.
    assert "crs" not in gj


def test_geometries_to_geojson_non_wgs84_records_crs():
    gj = geometries_to_geojson([Point(0, 0)], crs="EPSG:3857")
    assert gj["crs"]["properties"]["name"] == "EPSG:3857"


def test_geographic_circle_area_positive_and_finite():
    poly = geographic_circle((0.0, 0.0), 500.0, segments=128)
    assert poly.area > 0
    assert math.isfinite(poly.area)
