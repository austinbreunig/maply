from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any, Union, Callable, Set, TypeVar, Generic, Iterable, Iterator, Sequence, Mapping
from shapely.geometry import (
    Polygon as ShapelyPolygon, 
    Point as ShapelyPoint, 
    LineString as ShapelyLineString, 
    MultiLineString as ShapelyMultiLineString,
    MultiPoint as ShapelyMultiPoint,
    MultiPolygon as ShapelyMultiPolygon
)
import geopandas as gpd
import pandas as pd
import numpy as np
import random


@dataclass
class Shape:
    coords: Optional[List[Tuple[float, float]]] = field(default_factory=list)
    data: Optional[dict] = field(default_factory=dict)

    def to_gdf(self) -> gpd.GeoDataFrame:
        """Convert shape to a GeoDataFrame."""
        gdf_dict = self.data or {}  # Use data if provided
        gdf_dict["geometry"] = self.geometry
        return gpd.GeoDataFrame([gdf_dict])
    
    @classmethod
    def random(cls, shape_type: str = None, bounds: Tuple[int, int] = (0, 100)) -> 'Shape':
        """Generate a random shape (Point, LineString, or Polygon)."""
        shape_type = shape_type or random.choice(["point", "line", "polygon"])  # Choose randomly if not provided
        
        if shape_type == "point":
            return Point(coords=(random.randint(*bounds), random.randint(*bounds)))

        elif shape_type == "line":
            num_points = random.randint(2, 5)  # Random number of line points
            coords = [(random.randint(*bounds), random.randint(*bounds)) for _ in range(num_points)]
            return Line(coords=coords)

        elif shape_type == "polygon":
            num_points = random.randint(3, 6)  # Random polygon (at least 3 points)
            points = []
            for _ in range(num_points):
                point = Point(coords=(random.randint(*bounds), random.randint(*bounds)))
                points.append(point.coords)

            coords = list(MultiPoint(points=points).geometry.convex_hull.exterior.coords)  # Create a convex hull to form a polygon

            return Polygon(coords=coords)  # Return the convex hull as a polygon

        else:
            raise ValueError(f"Unknown shape type: {shape_type}")
        
        
@dataclass
class Polygon(Shape):
    origin: Optional[Tuple[float, float]] = field(default=None)
    size: Optional[Tuple[float, float]] = field(default=None)
    interior : Optional[List[List[float]]] = field(default=None)  # For holes in the polygon
    geometry: object = field(init=False)
    
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
        
        holes = self.interior or []
        self.geometry = ShapelyPolygon(self.coords, holes=holes)

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
    polygons: List[Union['Polygon', List[List[float]]]] = field(default_factory=list)
    geometry: object = field(init=False)
    

    def __post_init__(self):
        """Convert input into a valid Shapely MultiPolygon."""
        processed_polygons = []
        
        for item in self.polygons:
            if isinstance(item, Polygon):  # If a Polygon instance, use its geometry
                processed_polygons.append(item.geometry)
            elif isinstance(item, list):  # If a list of coordinates, create a Polygon
                processed_polygons.append(ShapelyPolygon(item))
            else:
                raise TypeError("MultiPolygon must be initialized with Polygon instances or coordinate lists.")

        self.geometry = ShapelyMultiPolygon(processed_polygons)
        geoms = list(self.geometry.geoms)  # Store the coordinates of the MultiPolygon for potential use
        self.coords = [list(geom.exterior.coords) for geom in geoms]  # Store the coordinates of the MultiPolygon for potential use



@dataclass
class Line(Shape):
    geometry: object = field(init=False)
    def __post_init__(self):
        if self.coords is None:
            raise ValueError("Must provide `coords`.")
        
        self.geometry = ShapelyLineString(self.coords)

@dataclass
class MultiLine(Shape):
    lines: List[Union['Line', List[Tuple[float, float]]]] = field(default_factory=list)
    geometry: object = field(init=False)
    

    def __post_init__(self):
        """Convert input into a valid Shapely MultiLineString."""
        processed_lines = []
        
        for item in self.lines:
            if isinstance(item, Line):
                processed_lines.append(item.geometry)
            elif isinstance(item, list):
                processed_lines.append(ShapelyLineString(item))
            else:
                raise TypeError("MultiLine must be initialized with Line instances or coordinate lists.")
            
        self.geometry = ShapelyMultiLineString(processed_lines)
        geoms = list(self.geometry.geoms)  # Store the coordinates of the MultiLineString for potential use
        self.coords = [list(geom.coords) for geom in geoms]  # Store the coordinates of the MultiLineString for potential use

@dataclass
class Point(Shape):
    geometry: object = field(init=False)
    def __post_init__(self):
        if self.coords is None:
            raise ValueError("Must provide `coords`.")
        
        self.geometry = ShapelyPoint(self.coords)

@dataclass
class MultiPoint(Shape):
    points: List[Union['Point', Tuple[float, float]]] = field(default_factory=list)
    geometry: object = field(init=False)
    

    def __post_init__(self):
        """Convert input into a valid Shapely MultiPoint."""
        processed_points = []
        
        for item in self.points:
            if isinstance(item, Point):
                processed_points.append(item.geometry)
            elif isinstance(item, tuple):
                processed_points.append(ShapelyPoint(item))
            else:
                raise TypeError("MultiPoint must be initialized with Point instances or coordinate tuples.")
            
        self.geometry = ShapelyMultiPoint(processed_points)
        geoms = list(self.geometry.geoms)
        self.coords = [list(geom.coords) for geom in geoms]



