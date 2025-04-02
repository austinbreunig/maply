import pytest
import geopandas as gpd
from shapely.geometry import Point as ShapelyPoint, Polygon as ShapelyPolygon
from maply.geometry import Point, Polygon as MyPolygon
from maply.plot import Map  # Replace with actual import path

class TestMap:

    def test_add_shape_to_map(self):
        shape = Point(coords=(5, 5), data={"label": "Center"})
        m = Map()
        m.add_shape(shape, layer="points", style={"color": "red"}, label="label")
        
        assert "points" in m.layers
        layer_data = m.layers["points"]["shapes"]
        assert layer_data[0]["data"] == shape
        assert m.layers["points"]["style"]["color"] == "red"

    def test_add_gdf_to_map(self):
        gdf = gpd.GeoDataFrame([{"geometry": ShapelyPoint(1, 1), "name": "A"}])
        m = Map()
        m.add_gdf(gdf, layer="cities", style={"color": "green"}, label="name")
        
        assert "cities" in m.layers
        assert m.layers["cities"]["shapes"][0]["data"].equals(gdf)

    def test_add_shape_no_label(self):
        shape = Point(coords=(2, 3))
        m = Map()
        m.add_shape(shape)
        assert "default" in m.layers
        assert m.layers["default"]["shapes"][0]["label"] is None

    def test_add_shape_updates_style(self):
        shape1 = Point(coords=(0, 0))
        shape2 = Point(coords=(1, 1))
        m = Map()
        m.add_shape(shape1, layer="layer1", style={"color": "blue"})
        m.add_shape(shape2, layer="layer1", style={"edgecolor": "black"})
        style = m.layers["layer1"]["style"]
        assert style["color"] == "blue"
        assert style["edgecolor"] == "black"

    def test_layer_shape_storage(self):
        poly = MyPolygon(origin=(0, 0), size=(1, 1), data={"label": "Block"})
        m = Map()
        m.add_shape(poly, layer="blocks", label="label")
        stored_shape = m.layers["blocks"]["shapes"][0]["data"]
        assert isinstance(stored_shape, MyPolygon)
        assert stored_shape.data["label"] == "Block"

    def test_plot_does_not_crash(self, monkeypatch):
        shape = Point(coords=(0, 0), data={"name": "Origin"})
        m = Map(title="Test Plot")
        m.add_shape(shape, label="name")

        # Patch plt.show to prevent actual rendering during test
        monkeypatch.setattr("matplotlib.pyplot.show", lambda: None)

        # This should execute without error
        m.plot()
