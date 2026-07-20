"""maply — a Jupyter widget for drawing shapes and exporting them as geometry.

Draw points, lines, polygons (with holes), rectangles, and circles on a blank
XY canvas, then pull them back into Python as shapely geometries, WKT strings,
GeoJSON, or a GeoDataFrame.

For drawing on a real interactive map, :class:`GeoCanvas` wraps ipyleaflet and
is available when the optional ``geo`` extra (``pip install maply[geo]``) is
installed.
"""

from typing import TYPE_CHECKING

from maply.model import DrawState, Shape
from maply.tools import Tool
from maply.transform import CanvasTransform
from maply.widget import MaplyCanvas

if TYPE_CHECKING:  # pragma: no cover - typing only
    from maply.geocanvas import GeoCanvas

__version__ = "0.1.0"

__all__ = [
    "MaplyCanvas",
    "GeoCanvas",
    "Shape",
    "DrawState",
    "Tool",
    "CanvasTransform",
    "__version__",
]


def __getattr__(name: str):
    """Lazily expose :class:`GeoCanvas` so importing maply never requires ipyleaflet."""
    if name == "GeoCanvas":
        try:
            from maply.geocanvas import GeoCanvas
        except ImportError as exc:  # pragma: no cover - depends on env
            raise ImportError(
                "GeoCanvas requires ipyleaflet. Install it with "
                "`pip install maply[geo]` or `pip install ipyleaflet`."
            ) from exc
        return GeoCanvas
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
