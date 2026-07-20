# maply — Implementation Plan

`maply` is a Jupyter notebook widget for interactively drawing shapes on an
abstract XY canvas and converting them to shapely / WKT / GeoJSON / GeoDataFrame.
It targets geospatial engineers building minimal reproducible examples and
prototyping spatial algorithms.

## Decisions

| Area | Decision |
| --- | --- |
| Widget stack | `ipycanvas` for the drawing surface + `ipywidgets` for the toolbar |
| Coordinate space | Abstract planar XY (no basemap, no CRS) |
| Shapes (v1) | Point, LineString, Polygon, Polygon-with-holes, MultiPolygon/collections, Rectangle, Circle |
| Output | shapely objects, WKT, GeoJSON, GeoDataFrame (geopandas optional) |
| Packaging | src-layout + `pyproject.toml` (hatchling) |

## Architecture

```
src/maply/
  __init__.py       exports MaplyCanvas, __version__
  tools.py          Tool enum (POINT/LINE/POLYGON/RECT/CIRCLE) + edit actions
  model.py          Shape dataclass + DrawState container
  transform.py      canvas-pixel <-> world-XY affine (Y flip, configurable extent)
  geometry.py       to_shapely / to_wkt / to_geojson / to_geodataframe (pure fns)
  render.py         draw finished + in-progress shapes + vertex handles on Canvas
  interaction.py    mouse state machine -> mutates DrawState
  widget.py         MaplyCanvas composite (Canvas + toolbar) + public API
```

### Key ideas
- The **model + geometry + transform** layers are pure Python and fully unit
  testable without a running kernel — build and test these first.
- A `Shape` stores its kind, an exterior ring, optional interior rings (holes),
  or a center+radius for circles.
- `transform.py` flips the Y axis so exported shapely coordinates are Y-up.
- Circles export as an N-segment polygon approximation.

## Risk
`ipycanvas` round-trips every mouse event to the kernel, which can be laggy for
freehand drawing. Mitigation: click-to-add-vertex interaction (not freehand) and
`hold_canvas` batched redraws. If latency is unacceptable, the geometry/model
layer can be reused unchanged behind an `anywidget` front end.

## Phases
0. **Scaffold** — pyproject, src layout, meta files, editable install.
1. **Model + geometry** (TDD, pure Python) — Shape, transform, conversions.
2. **Render** — draw shapes / in-progress / handles via `hold_canvas`.
3. **Interaction** — tool state machine wired to Canvas mouse events.
4. **Public API + toolbar** — `MaplyCanvas`, tool buttons, undo/clear/export.
5. **Example** — `examples/quickstart.ipynb`.
6. **Tests + CI** — pytest for pure layers; ruff lint.

## Verification
- `pip install -e ".[dev]"` succeeds; `import maply` works.
- `pytest` green for geometry/transform/interaction.
- Manual: draw each shape type in the notebook, confirm
  `shapely.wkt.loads(canvas.wkt[i])` round-trips.
- `to_geodataframe()` raises a clear error when geopandas is absent.
