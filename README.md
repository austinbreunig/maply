# maply

**maply** is a Jupyter notebook widget for quickly *drawing* shapes on a blank
XY canvas and converting them into [shapely](https://shapely.readthedocs.io/)
geometries, WKT strings, GeoJSON, or a GeoDataFrame.

It is built for geospatial engineers who need to prototype and test spatial
algorithms, and want a fast way to hand-craft geometry for minimal reproducible
examples — without typing out coordinate tuples by hand.

## Features

- Draw **points, lines, polygons (with holes), rectangles, and circles** on an
  abstract XY canvas.
- Build **multipart** geometries / collections.
- Pull results straight into Python:
  - `canvas.geometries` → list of shapely geometries
  - `canvas.wkt` → WKT strings
  - `canvas.geojson` → GeoJSON dict
  - `canvas.to_geodataframe()` → geopandas `GeoDataFrame` (optional dependency)
- Or draw on a **real interactive map** with `GeoCanvas` (ipyleaflet), including
  pushing Python geometry back onto the map to inspect and edit it.

## Install

```bash
pip install -e .              # core
pip install -e ".[geopandas]" # + GeoDataFrame export
pip install -e ".[geo]"       # + GeoCanvas interactive map (ipyleaflet)
pip install -e ".[dev]"       # + test / lint tooling
```

## Quick start

```python
from maply import MaplyCanvas

canvas = MaplyCanvas(width=600, height=400)
canvas          # draw shapes interactively in the output cell

canvas.wkt          # -> ['POLYGON ((...))', 'POINT (...)']
canvas.geometries   # -> [<shapely Polygon>, <shapely Point>]
```

### Draw on a real map

`GeoCanvas` wraps an [ipyleaflet](https://ipyleaflet.readthedocs.io) map (pan,
zoom, basemaps, draw/edit toolbar) and connects it to the same conversion layer
— in **both directions**:

```python
from shapely.geometry import Polygon
from maply import GeoCanvas

geo = GeoCanvas(center=(37.77, -122.42), zoom=12)

# Python -> map: inspect / edit a geometry on the map
geo.add_geometry(Polygon([(-122.45, 37.75), (-122.40, 37.75),
                          (-122.40, 37.79), (-122.45, 37.79)]))
geo

# map -> Python (after drawing/editing)
geo.wkt
geo.to_geodataframe(crs="EPSG:3857")   # optional reprojection
```

See [`examples/quickstart.ipynb`](examples/quickstart.ipynb) for a full walkthrough.

## Status

Alpha. `MaplyCanvas` uses planar XY (no CRS). `GeoCanvas` draws in lon/lat
(EPSG:4326) on a live map and is available with the `geo` extra.

