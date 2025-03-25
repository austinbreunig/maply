from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Union
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import matplotlib.lines as mlines
from geometry import Shape  # Import your Shape class and its subclasses
import geopandas as gpd

@dataclass
class Map:
    # Layers: each layer holds a list of items (each is a dict with keys:
    # "source" (either "shape" or "gdf"), "data" (the Shape or GeoDataFrame),
    # "label", and "label_kwargs"), and a "style" dict.
    layers: Dict[str, Dict[str, Any]] = field(
        default_factory=dict
    )
    title: str = "My Map"
    figsize: Tuple[int, int] = (10, 10)

    def add_shape(
        self, 
        shape: Shape, 
        layer: str = "default", 
        style: Optional[Dict[str, Any]] = None,
        label: Optional[Union[bool, str]] = None,
        label_kwargs: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a Shape instance to a specific layer.
        
        - The `style` dict holds plotting options.
        - The `label` parameter can be:
            - True: then the code will look for a "label" key in shape.data.
            - A string: which is used as a key to extract a label from shape.data.
        - The `label_kwargs` dict allows you to control text appearance (e.g., color, alignment).
        """
        if layer not in self.layers:
            self.layers[layer] = {"shapes": [], "style": style or {}}
        self.layers[layer]["shapes"].append({
            "source": "shape",
            "data": shape,
            "label": label,
            "label_kwargs": label_kwargs or {}
        })
        if style:
            self.layers[layer]["style"].update(style)
    
    def add_gdf(
        self,
        gdf: gpd.GeoDataFrame,
        layer: str = "default",
        style: Optional[Dict[str, Any]] = None,
        label: Optional[Union[bool, str]] = None,
        label_kwargs: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a GeoDataFrame to a specific layer.
        
        - The parameters work the same as in add_shape.
        - When plotting, the GeoDataFrame will be used directly.
        """
        if layer not in self.layers:
            self.layers[layer] = {"shapes": [], "style": style or {}}
        self.layers[layer]["shapes"].append({
            "source": "gdf",
            "data": gdf,
            "label": label,
            "label_kwargs": label_kwargs or {}
        })
        if style:
            self.layers[layer]["style"].update(style)
    
    def plot(self) -> None:
        """
        Plot all layers using matplotlib.
        
        - The legend always displays the layer names.
        - For each item, if a label is provided, a text annotation is drawn at the centroid.
          The default text style can be overridden with label_kwargs.
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        for layer_name, info in self.layers.items():
            for item in info["shapes"]:
                source_type = item["source"]
                label = item["label"]
                # Get the GeoDataFrame and geometry from the source.
                if source_type == "shape":
                    shape = item["data"]
                    gdf = shape.to_gdf()
                    geom = shape.geometry
                elif source_type == "gdf":
                    gdf = item["data"]
                    geom = gdf.unary_union  # Combine all geometries to compute a centroid
                else:
                    continue
                
                # Copy the layer's style options.
                plot_kwargs = dict(info["style"])
                gdf.plot(ax=ax, **plot_kwargs)
                
                # Handle label if provided.
                if isinstance(label, str):
                    # Default label styling options.
                    default_label_kwargs = {
                        "horizontalalignment": "center",
                        "verticalalignment": "center",
                        "fontsize": 10,
                        "color": "black",
                        "weight": "bold"
                    }

                    if source_type == "shape":
                        text_label = shape.data.get(label, "")
                        centroid = geom.centroid
                        default_label_kwargs.update(item["label_kwargs"])
                        ax.text(centroid.x, centroid.y, text_label, **default_label_kwargs)

                    elif source_type == "gdf":
                        # Iterate through each row in the GeoDataFrame and annotate using the column specified by label.
                        for idx, row in gdf.iterrows():
                            centroid = row.geometry.centroid
                            text_label = row[label]  # 'label' is the name of the column to use.
                            ax.text(centroid.x, centroid.y, text_label, **default_label_kwargs)

                    else:
                        continue
        
        # Build legend proxies for each layer.
        legend_proxies = []
        for layer_name, info in self.layers.items():
            style = info["style"]
            source_type = info["shapes"][0].get("source")
            color = style.get("color", "blue")
            if source_type == "shape":
                geometry = info["shapes"][0]["data"].geometry
            elif source_type == "gdf":
                geometry = info
        
        # Create a proxy patch for legend.
            if hasattr(geometry, 'geom_type'):
                if geometry.geom_type == 'Polygon' or geometry.geom_type == 'MultiPolygon':
                    geom_type = 'Polygon'
                elif geometry.geom_type == 'LineString' or geometry.geom_type == 'MultiLineString':
                    geom_type = 'Line'
                elif geometry.geom_type == 'Point' or geometry.geom_type == 'MultiPoint':
                    geom_type = 'Point'
                else:
                    geom_type = 'Other'
            else:
                geom_type = 'Other'

            if geom_type == 'Polygon':
                proxy = Patch(
                    facecolor=style.get("facecolor", "blue"),
                    edgecolor=style.get("edgecolor", "black"),
                    label=layer_name
                )

            elif geom_type == 'Line':
                proxy = mlines.Line2D([], [], color=color, label=layer_name)

            elif geom_type == 'Point':
                proxy = mlines.Line2D([], [], marker='o', color='w', label=layer_name, markerfacecolor=color)
                
            else:
                proxy = Patch(
                    facecolor=style.get("facecolor", "blue"),
                    edgecolor=style.get("edgecolor", "black"),
                    label=layer_name
                )

            legend_proxies.append(proxy)
        
        ax.legend(handles=legend_proxies, loc='upper left')
        ax.set_title(self.title)
        plt.show()


