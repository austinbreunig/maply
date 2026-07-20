# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-07-20

### Added
- `MaplyCanvas` / `XYCanvas`: draw points, lines, polygons (with holes),
  rectangles, and circles on an abstract XY canvas.
- Export drawn shapes as shapely geometries, WKT, GeoJSON, a
  `GeometryCollection`, or a geopandas `GeoDataFrame`.
- `GeoCanvas`: draw on an interactive ipyleaflet map with a Geoman
  draw/edit/delete toolbar, plus push shapely / WKT / GeoDataFrame geometry back
  onto the map (available via the `geo` extra).

[Unreleased]: https://github.com/austinbreunig/maply/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/austinbreunig/maply/releases/tag/v0.1.0
