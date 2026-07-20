"""Convert :class:`~maply.model.Shape` objects into geometry representations.

These functions are pure and have no dependency on the widget or a running
Jupyter kernel, which makes them straightforward to unit test.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from shapely.geometry import (
    GeometryCollection,
    LineString,
    Point,
    Polygon,
)
from shapely.geometry import (
    mapping as shapely_mapping,
)
from shapely.geometry import (
    shape as shapely_shape,
)

from maply.model import Shape
from maply.tools import Tool

if TYPE_CHECKING:  # pragma: no cover - typing only
    from shapely.geometry.base import BaseGeometry

# Number of segments used to approximate a circle as a polygon.
CIRCLE_SEGMENTS = 64
# Approximate metres per degree of latitude (spherical earth).
_METERS_PER_DEGREE = 111_320.0


def circle_to_polygon(
    center: tuple[float, float], radius: float, segments: int = CIRCLE_SEGMENTS
) -> Polygon:
    """Approximate a circle as a regular polygon with ``segments`` sides."""
    if radius <= 0:
        raise ValueError("circle radius must be positive")
    if segments < 3:
        raise ValueError("a circle approximation needs at least 3 segments")
    cx, cy = center
    coords = [
        (
            cx + radius * math.cos(2 * math.pi * i / segments),
            cy + radius * math.sin(2 * math.pi * i / segments),
        )
        for i in range(segments)
    ]
    return Polygon(coords)


def shape_to_geometry(shape: Shape) -> BaseGeometry:
    """Convert a single :class:`Shape` into a shapely geometry.

    Raises :class:`ValueError` if the shape does not have enough vertices to
    form a valid geometry.
    """
    if not shape.is_valid():
        raise ValueError(f"{shape.kind.label} shape does not have enough vertices")

    if shape.kind is Tool.POINT:
        return Point(shape.exterior[0])
    if shape.kind is Tool.LINE:
        return LineString(shape.exterior)
    if shape.kind in (Tool.POLYGON, Tool.RECT):
        return Polygon(shape.exterior, holes=shape.holes or None)
    if shape.kind is Tool.CIRCLE:
        assert shape.center is not None and shape.radius is not None
        return circle_to_polygon(shape.center, shape.radius)

    raise ValueError(f"unsupported shape kind: {shape.kind!r}")


def to_shapely(shapes: list[Shape]) -> list[BaseGeometry]:
    """Convert every valid shape into a shapely geometry.

    Invalid shapes are skipped rather than raising, so a half-finished draft
    never breaks export.
    """
    return [shape_to_geometry(s) for s in shapes if s.is_valid()]


# ---------------------------------------------------------------------------
# Shared export core — operates on plain shapely geometries so both the
# ``Shape``-based ``XYCanvas`` and the GeoJSON-based ``GeoCanvas`` can reuse it.
# ---------------------------------------------------------------------------


def _is_wgs84(crs: str | None) -> bool:
    return crs is None or crs.upper() in ("EPSG:4326", "WGS84", "CRS84")


def geometries_to_wkt(geometries: list[BaseGeometry]) -> list[str]:
    """Return the WKT string for every geometry."""
    return [geom.wkt for geom in geometries]


def geometries_to_collection(geometries: list[BaseGeometry]) -> GeometryCollection:
    """Bundle geometries into a single :class:`GeometryCollection`."""
    return GeometryCollection(list(geometries))


def geometries_to_geojson(
    geometries: list[BaseGeometry],
    kinds: list[str] | None = None,
    crs: str | None = None,
) -> dict[str, Any]:
    """Return a GeoJSON ``FeatureCollection`` for the given geometries.

    ``kinds`` optionally supplies a per-geometry ``"kind"`` property. ``crs`` is
    recorded in a top-level ``"crs"`` member only when it is not WGS84 (GeoJSON
    coordinates are assumed to be WGS84 per RFC 7946).
    """
    kinds = kinds if kinds is not None else [None] * len(geometries)
    features = []
    for geom, kind in zip(geometries, kinds):
        properties = {} if kind is None else {"kind": kind}
        features.append(
            {
                "type": "Feature",
                "properties": properties,
                "geometry": shapely_mapping(geom),
            }
        )
    collection: dict[str, Any] = {"type": "FeatureCollection", "features": features}
    if not _is_wgs84(crs):
        collection["crs"] = {"type": "name", "properties": {"name": crs}}
    return collection


def geometries_to_geodataframe(
    geometries: list[BaseGeometry],
    kinds: list[str] | None = None,
    crs: str | None = None,
):  # noqa: ANN201 - optional return type
    """Return a geopandas ``GeoDataFrame`` for the given geometries.

    Requires the optional ``geopandas`` dependency. Raises a clear
    :class:`ImportError` if it is not installed. ``crs`` (e.g. ``"EPSG:4326"``)
    is attached to the frame when supplied.
    """
    try:
        import geopandas as gpd
    except ImportError as exc:  # pragma: no cover - depends on env
        raise ImportError(
            "to_geodataframe() requires geopandas. Install it with "
            "`pip install maply[geopandas]` or `pip install geopandas`."
        ) from exc

    geometries = list(geometries)
    data = {} if kinds is None else {"kind": list(kinds)}
    return gpd.GeoDataFrame(data, geometry=geometries, crs=crs)


# ---------------------------------------------------------------------------
# GeoJSON -> shapely (the map -> Python direction for ``GeoCanvas``).
# ---------------------------------------------------------------------------


def geographic_circle(
    center: tuple[float, float], radius_m: float, segments: int = CIRCLE_SEGMENTS
) -> Polygon:
    """Approximate a ground circle (radius in metres) as a lon/lat polygon.

    Uses a local equirectangular approximation so no projection library is
    required. Accurate enough for prototyping away from the poles.
    """
    if radius_m <= 0:
        raise ValueError("circle radius must be positive")
    lon, lat = center
    dlat = radius_m / _METERS_PER_DEGREE
    dlon = radius_m / (_METERS_PER_DEGREE * max(math.cos(math.radians(lat)), 1e-9))
    coords = [
        (
            lon + dlon * math.cos(2 * math.pi * i / segments),
            lat + dlat * math.sin(2 * math.pi * i / segments),
        )
        for i in range(segments)
    ]
    return Polygon(coords)


def geojson_feature_to_geometry(feature: dict[str, Any]) -> BaseGeometry:
    """Convert a single GeoJSON feature (or geometry) to a shapely geometry.

    Handles the leaflet/Geoman convention where a *circle* is emitted as a
    ``Point`` feature carrying a ``radius`` (metres) property: such features are
    polygonised via :func:`geographic_circle`.
    """
    geom = feature.get("geometry", feature)
    properties = feature.get("properties") or {}
    radius = properties.get("radius")
    if radius and geom.get("type") == "Point":
        lon, lat = geom["coordinates"]
        return geographic_circle((lon, lat), float(radius))
    return shapely_shape(geom)


def features_to_geometries(features: list[dict[str, Any]]) -> list[BaseGeometry]:
    """Convert a list of GeoJSON features to shapely geometries."""
    return [geojson_feature_to_geometry(f) for f in features]


# ---------------------------------------------------------------------------
# ``Shape``-based API (unchanged public behaviour) — thin wrappers over the
# shared core above.
# ---------------------------------------------------------------------------


def to_wkt(shapes: list[Shape]) -> list[str]:
    """Return the WKT string for every valid shape."""
    return geometries_to_wkt(to_shapely(shapes))


def to_collection(shapes: list[Shape]) -> GeometryCollection:
    """Bundle all valid shapes into a single :class:`GeometryCollection`."""
    return geometries_to_collection(to_shapely(shapes))


def to_geojson(shapes: list[Shape]) -> dict[str, Any]:
    """Return a GeoJSON ``FeatureCollection`` for all valid shapes."""
    valid = [s for s in shapes if s.is_valid()]
    return geometries_to_geojson(
        [shape_to_geometry(s) for s in valid],
        kinds=[s.kind.value for s in valid],
    )


def to_geodataframe(shapes: list[Shape]):  # noqa: ANN201 - optional return type
    """Return a geopandas ``GeoDataFrame`` of all valid shapes.

    Requires the optional ``geopandas`` dependency. Raises a clear
    :class:`ImportError` if it is not installed.
    """
    valid = [s for s in shapes if s.is_valid()]
    return geometries_to_geodataframe(
        [shape_to_geometry(s) for s in valid],
        kinds=[s.kind.value for s in valid],
    )
