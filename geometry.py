from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from shapely.geometry import (
    Polygon as ShapelyPolygon, 
    Point as ShapelyPoint, 
    LineString as ShapelyLineString, 
    MultiPolygon as ShapelyMultiPolygon
)
import geopandas as gpd
import pandas as pd
import numpy as np
import random

@dataclass
class Shape:
    coords: Optional[List[Tuple[float, float]]] = field(default=None)
    data: Optional[dict] = None

    def to_gdf(self) -> gpd.GeoDataFrame:
        """Convert shape to a GeoDataFrame."""
        gdf_dict = self.data or {}  # Use data if provided
        gdf_dict["geometry"] = self.geometry
        return gpd.GeoDataFrame([gdf_dict])

@dataclass
class Polygon(Shape):
    origin: Optional[Tuple[float, float]] = None
    size: Optional[Tuple[float, float]] = None
    def __post_init__(self):
        if self.origin is not None and self.size is not None:
            self.coords = [
                self.origin,
                (self.origin[0] + self.size[0], self.origin[1]),
                (self.origin[0] + self.size[0], self.origin[1] + self.size[1]),
                (self.origin[0], self.origin[1] + self.size[1]),
            ]
        elif self.coords is not None:
            pass  # Use given coords
        else:
            raise ValueError("Must provide either `origin` and `size`, or `coords`.")
        
        self.geometry = ShapelyPolygon(self.coords)

    def split_grid(self, rows: int, cols: int) -> List['Polygon']:
        """Splits the polygon into a grid of `rows x cols` smaller polygons."""
        if self.size is None or self.origin is None:
            raise ValueError("Grid splitting requires `origin` and `size`.")

        width, height = self.size[0] / cols, self.size[1] / rows
        sub_polygons = []

        for i in range(rows):
            for j in range(cols):
                sub_origin = (self.origin[0] + j * width, self.origin[1] + i * height)
                sub_polygons.append(Polygon(origin=sub_origin, size=(width, height)))

        return sub_polygons

@dataclass
class MultiPolygon(Shape):
    def __post_init__(self):
        if self.coords is None:
            raise ValueError("Must provide `coords`.")
        
        self.geometry = ShapelyPolygon(self.coords)

@dataclass
class Line(Shape):
    def __post_init__(self):
        if self.coords is None:
            raise ValueError("Must provide `coords`.")
        
        self.geometry = ShapelyLineString(self.coords)