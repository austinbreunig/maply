import pytest
from shapely.geometry import Polygon as ShapelyPolygon
from maply.geometry import Shape, Point, Line, Polygon, MultiPolygon, MultiLine, MultiPoint

class TestGeometry:

    def test_point_creation(self):
        pt = Point(coords=(10, 20))
        assert pt.geometry.x == 10
        assert pt.geometry.y == 20
        assert pt.to_gdf().geometry.iloc[0].equals(pt.geometry)

    def test_line_creation(self):
        coords = [(0, 0), (1, 1), (2, 2)]
        line = Line(coords=coords)
        assert line.geometry.length > 0
        assert line.to_gdf().geometry.iloc[0].equals(line.geometry)

    def test_polygon_from_coords(self):
        coords = [(0, 0), (1, 0), (1, 1), (0, 1)]
        poly = Polygon(coords=coords)
        assert isinstance(poly.geometry, ShapelyPolygon)
        assert poly.geometry.is_valid
        assert poly.to_gdf().geometry.iloc[0].equals(poly.geometry)

    def test_polygon_from_origin_size(self):
        poly = Polygon(origin=(0, 0), size=(2, 2))
        assert poly.geometry.bounds == (0, 0, 2, 2)
        assert poly.to_gdf().geometry.iloc[0].equals(poly.geometry)

    def test_polygon_grid_split(self):
        poly = Polygon(origin=(0, 0), size=(4, 4))
        grid = poly.split_grid(rows=2, cols=2)
        assert len(grid) == 4
        for sub in grid:
            assert sub.size == (2.0, 2.0)

    def test_multipolygon_creation(self):
        p1 = Polygon(origin=(0, 0), size=(1, 1))
        p2 = Polygon(origin=(2, 2), size=(1, 1))
        mp = MultiPolygon(polygons=[p1, p2])
        assert len(mp.geometry.geoms) == 2
        assert mp.to_gdf().geometry.iloc[0].equals(mp.geometry)

    def test_multiline_creation(self):
        l1 = Line(coords=[(0, 0), (1, 1)])
        l2 = Line(coords=[(2, 2), (3, 3)])
        ml = MultiLine(lines=[l1, l2])
        assert len(ml.geometry.geoms) == 2
        assert ml.to_gdf().geometry.iloc[0].equals(ml.geometry)

    def test_multipoint_creation(self):
        p1 = Point(coords=(0, 0))
        p2 = Point(coords=(1, 1))
        mp = MultiPoint(points=[p1, p2])
        assert len(mp.geometry.geoms) == 2
        assert mp.to_gdf().geometry.iloc[0].equals(mp.geometry)

    def test_random_shape_generation(self):
        shape = Shape.random()
        assert isinstance(shape, Shape)
        assert hasattr(shape, 'geometry')
        assert shape.to_gdf().geometry.iloc[0].equals(shape.geometry)

    def test_random_point_generation(self):
        shape = Shape.random("point")
        assert isinstance(shape, Point)

    def test_random_line_generation(self):
        shape = Shape.random("line")
        assert isinstance(shape, Line)
        assert len(shape.coords) >= 2

    def test_random_polygon_generation(self):
        shape = Shape.random("polygon")
        assert isinstance(shape, Polygon)
        assert shape.geometry.is_valid
