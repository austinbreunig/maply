# maply: spatial prototyping made easy

## Introduction
maply allows you to quickly build shapes, utilize geospatial operations, and plot. It serves as a wrapper to geopandas, shapely, and matplotlib, making it a straight-forward, no-frills, "*minimal-reproducible-example*" for building proof-of-concept and testing your algorithms.
## Installation
1. Find the **latest** release [here.](https://github.com/austinbreunig/maply/releases)
2. Download wheel
3. pip install the wheel

**Package uses:**

python >= 3.6

geopandas

shapely

numpy

matplotlib

## Quick Start

### Creating a Maply Polygon using origin & size
```
polygon = Polygon(origin=(0,0), size=(2,2))

>>> Polygon(coords=[(0, 0), (2, 0), (2, 2), (0, 2)], data={}, origin=(0, 0), size=(2, 2), interior=None, geometry=<POLYGON ((0 0, 2 0, 2 2, 0 2, 0 0))>)
```
### Creating a Maply Polygon using coords
```
 polygon = Polygon(coords=[(0,0),(0,2),(2,2),(0,2)])

>>> Polygon(coords=[(0, 0), (0, 2), (2, 2), (0, 2)], data={}, origin=None, size=None, interior=None, geometry=<POLYGON ((0 0, 0 2, 2 2, 0 2, 0 0))>)
```

### Maply Polygon to Geodataframe
```
polygon = Polygon(coords=[(0,0),(0,2),(2,2),(0,2)], data={'Shape':'Square'})

polygon.to_gdf()

>>> 
    Shape                             geometry
0  Square  POLYGON ((0 0, 0 2, 2 2, 0 2, 0 0))
```
### Plotting a Maply Polygon
```
from maply.plot import Map

m = Map()

m.add_shape(polygon)

m.plot(label='Shape')

```

## Example Notebook
- [Spatial Join](examples\spatial_join.ipynb)