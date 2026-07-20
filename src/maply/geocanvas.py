"""The :class:`GeoCanvas` widget — draw shapes on a real ipyleaflet map.

Unlike :class:`~maply.widget.XYCanvas` (which draws on an abstract plane),
``GeoCanvas`` embeds a fully interactive `ipyleaflet <https://ipyleaflet.readthedocs.io>`_
map: pan, zoom, basemaps, and a Geoman draw/edit/delete toolbar all come from
ipyleaflet. maply's contribution is the **pure-Python glue** on both sides:

- map -> Python: drawn features become shapely / WKT / GeoJSON / GeoDataFrame.
- Python -> map: shapely geometries, WKT, or a GeoDataFrame can be pushed onto
  the map (optionally editable) — e.g. to inspect a spatial algorithm's output.

Coordinates are geographic (lon/lat, EPSG:4326). ``ipyleaflet`` is an optional
dependency; install it with ``pip install maply[geo]``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

import ipywidgets as widgets
from ipyleaflet import GeoJSON, GeomanDrawControl, Map, basemaps
from shapely import wkt as shapely_wkt
from shapely.geometry import mapping as shapely_mapping
from shapely.geometry import shape as shapely_shape

from maply import geometry

if TYPE_CHECKING:  # pragma: no cover - typing only
    from shapely.geometry.base import BaseGeometry

_WGS84 = "EPSG:4326"


def _to_shapely(geom: Any) -> BaseGeometry:
    """Coerce a shapely geometry, WKT string, or GeoJSON mapping to shapely."""
    if isinstance(geom, str):
        return shapely_wkt.loads(geom)
    if hasattr(geom, "__geo_interface__"):
        return shapely_shape(geom.__geo_interface__)
    if isinstance(geom, dict):
        return shapely_shape(geom)
    raise TypeError(f"cannot interpret {type(geom)!r} as a geometry")


def _feature(geom: BaseGeometry, kind: str | None, style: dict[str, Any]) -> dict[str, Any]:
    properties: dict[str, Any] = dict(style)
    if kind is not None:
        properties["kind"] = kind
    return {
        "type": "Feature",
        "properties": properties,
        "geometry": shapely_mapping(geom),
    }


class GeoCanvas(widgets.VBox):
    """Interactive geographic shape-drawing widget backed by ipyleaflet.

    Parameters
    ----------
    center:
        Initial map centre as ``(lat, lon)``.
    zoom:
        Initial zoom level.
    basemap:
        An ipyleaflet basemap. Defaults to OpenStreetMap.
    width, height:
        CSS sizes for the map (e.g. ``"100%"``, ``"500px"``).
    crs:
        The CRS drawn coordinates are reported in. Leaflet works in lon/lat, so
        this should stay ``"EPSG:4326"``.
    """

    def __init__(
        self,
        center: tuple[float, float] = (0.0, 0.0),
        zoom: int = 2,
        *,
        basemap: Any | None = None,
        width: str = "100%",
        height: str = "500px",
        crs: str = _WGS84,
    ):
        self._crs = crs
        self.map = Map(
            center=center,
            zoom=zoom,
            basemap=basemap or basemaps.OpenStreetMap.Mapnik,
            scroll_wheel_zoom=True,
        )
        self.map.layout.width = width
        self.map.layout.height = height

        self.draw_control = GeomanDrawControl()
        self.map.add(self.draw_control)

        # GeoJSON / GeoData layers added via the Python -> map helpers.
        self._extra_layers: list[Any] = []

        super().__init__([self.map])

    # -- events -----------------------------------------------------------

    def on_draw(self, callback: Callable, remove: bool = False) -> None:
        """Register a callback fired on draw/edit/delete (see ipyleaflet)."""
        self.draw_control.on_draw(callback, remove=remove)

    # -- map -> Python ----------------------------------------------------

    @property
    def features(self) -> list[dict[str, Any]]:
        """The raw GeoJSON features currently on the draw layer."""
        return list(self.draw_control.data)

    @property
    def geometries(self) -> list[BaseGeometry]:
        """Drawn features as shapely geometries (circles are polygonised)."""
        return geometry.features_to_geometries(self.draw_control.data)

    @property
    def wkt(self) -> list[str]:
        """WKT strings for the drawn features."""
        return geometry.geometries_to_wkt(self.geometries)

    @property
    def geojson(self) -> dict[str, Any]:
        """A GeoJSON ``FeatureCollection`` of the drawn features."""
        return {"type": "FeatureCollection", "features": list(self.draw_control.data)}

    def to_collection(self):
        """Bundle the drawn features into a shapely ``GeometryCollection``."""
        return geometry.geometries_to_collection(self.geometries)

    def to_geodataframe(self, crs: str | None = None):
        """Return a geopandas ``GeoDataFrame`` of the drawn features.

        The frame is created in the canvas CRS (WGS84). Pass ``crs`` to
        reproject the result (requires geopandas/pyproj).
        """
        kinds = [
            (f.get("geometry") or {}).get("type") for f in self.draw_control.data
        ]
        gdf = geometry.geometries_to_geodataframe(self.geometries, kinds=kinds, crs=self._crs)
        if crs is not None and crs != self._crs:
            gdf = gdf.to_crs(crs)
        return gdf

    # -- Python -> map ----------------------------------------------------

    def add_geometry(
        self,
        geom: Any,
        *,
        editable: bool = True,
        kind: str | None = None,
        **style: Any,
    ) -> dict[str, Any]:
        """Add a shapely geometry / WKT / GeoJSON to the map.

        When ``editable`` is true the feature is placed on the Geoman draw layer
        so it can be moved, reshaped, or deleted (and will show up in
        :attr:`geometries`). Otherwise it is added as a static ``GeoJSON`` layer.
        """
        feature = _feature(_to_shapely(geom), kind, style if not editable else {})
        if editable:
            self.draw_control.data = [*self.draw_control.data, feature]
        else:
            layer = GeoJSON(data={"type": "FeatureCollection", "features": [feature]})
            self.map.add(layer)
            self._extra_layers.append(layer)
        return feature

    def add_wkt(self, wkt: str, **kwargs: Any) -> dict[str, Any]:
        """Add a geometry from a WKT string. See :meth:`add_geometry`."""
        return self.add_geometry(shapely_wkt.loads(wkt), **kwargs)

    def add_geodataframe(self, gdf: Any, *, editable: bool = False, **style: Any) -> None:
        """Add every geometry in a GeoDataFrame to the map.

        Reprojects to WGS84 first. Non-editable by default (a single static
        layer is far lighter than many editable Geoman features).
        """
        if getattr(gdf, "crs", None) is not None and str(gdf.crs).upper() not in (
            "EPSG:4326",
            "WGS84",
        ):
            gdf = gdf.to_crs(_WGS84)
        if editable:
            new = [_feature(geom, None, {}) for geom in gdf.geometry]
            self.draw_control.data = [*self.draw_control.data, *new]
        else:
            layer = GeoJSON(data=gdf.__geo_interface__, style=style or {})
            self.map.add(layer)
            self._extra_layers.append(layer)

    def clear(self) -> None:
        """Remove all drawn features and injected layers."""
        self.draw_control.clear()
        self.draw_control.data = []
        for layer in self._extra_layers:
            try:
                self.map.remove(layer)
            except Exception:  # noqa: BLE001 - layer may already be gone
                pass
        self._extra_layers.clear()
