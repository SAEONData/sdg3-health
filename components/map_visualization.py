from operator import le
import streamlit as st
import geopandas as gpd
import folium
import numpy as np
from streamlit_folium import st_folium
from branca.element import Template, MacroElement
import pandas as pd
from data.queries import GeographicQueries
from config.settings import MAP_CONFIG, MAP_LAYERS
from typing import Dict, Optional

class MapVisualization:
    """Auto-zoomed map component for Home page"""
    
    def __init__(self):
        self.spatial_queries = GeographicQueries()
        self.default_center = [MAP_CONFIG["center_lat"], MAP_CONFIG["center_lon"]]
        self.default_zoom = MAP_CONFIG["default_zoom"]
    
    def render_map(self, geographic_selection: Dict, selected_indicator: str = "Health_worker_density__index_") -> folium.Map:
        """Render the main map based on geographic selection"""
        
        map_data = self._get_map_data(geographic_selection)
        
        if map_data is None or map_data.empty:
            return self._create_default_map()
        
        center_coords = self._get_map_center(map_data)
        zoom_level = self._get_zoom_level(geographic_selection["level"])
        
        m = folium.Map(
            location=center_coords,
            zoom_start=zoom_level,
            tiles='OpenStreetMap',
            width='100%',
            height=MAP_CONFIG["map_height"]
        )
        
        self._add_choropleth_layer(m, map_data, selected_indicator)
        
        if geographic_selection["level"] == "municipality":
            self._add_neighboring_context(m, geographic_selection)
        
        return m
    
    def render_layer_toggles(self) -> str:
        """Render map layer toggle controls"""
        
        st.markdown("### 🗺️ Map Layers")
        
        layer_options = {
            "Health_worker_density__index_": "🏥 Health Worker Density",
            "Total_living_with_HIV": "🦠 HIV Cases", 
            "TB_DS_treatment_success_rate": "🫁 TB Treatment Success",
            "Number_of_health_facilities": "🏗️ Health Facilities",
            "Total_population": "👥 Population Density"
        }
        
        selected_layer = st.selectbox(
            "Select Indicator:",
            options=list(layer_options.keys()),
            format_func=lambda x: layer_options[x],
            key="map_layer_selector",
            help="Choose which health indicator to display on the map"
        )
        
        return selected_layer
    

    def _get_map_data(self, geographic_selection: Dict) -> Optional[gpd.GeoDataFrame]:
        """Get spatial data based on geographic selection level"""
        
        level = geographic_selection["level"]
        
        if level == "national":
            return self.spatial_queries.get_province_boundaries()
            
        elif level == "province":
            return self.spatial_queries.get_district_boundaries(
                geographic_selection["province_code"]
            )
            
        elif level == "district":
            return self.spatial_queries.get_municipality_boundaries(
                geographic_selection["district_code"]
            )
            
        elif level == "municipality":
            return self.spatial_queries.get_municipality_with_neighbors(
                geographic_selection["municipality_code"]
            )
        
        return None
    
    def _get_map_center(self, gdf: gpd.GeoDataFrame) -> list:
        """Calculate map center from geometry bounds"""
        bounds = gdf.total_bounds
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2
        return [center_lat, center_lon]
    

    def _get_zoom_level(self, geographic_level: str) -> int:
        """Determine appropriate zoom level based on geographic selection"""
        zoom_levels = {
            "national": 5,
            "province": 7,
            "district": 9,
            "municipality": 11
        }
        return zoom_levels.get(geographic_level, MAP_CONFIG["default_zoom"])
    

    def _add_custom_legend(self, map_obj, title, color_scheme, min_val, max_val, indicator_column):
        """Add custom HTML legend with formatted tick labels and matching gradient"""
        
        formatted_min = self._format_legend_number(min_val, indicator_column)
        formatted_max = self._format_legend_number(max_val, indicator_column)

        color_gradients = {
            "Reds": "#fee5d9, #fb6a4a, #a50f15",
            "Greens": "#e5f5e0, #a1d99b, #006d2c",
            "Blues": "#deebf7, #9ecae1, #084594",
            "Purples": "#efedf5, #9e9ac8, #54278f",
            "YlOrRd": "#ffffb2, #fecc5c, #e31a1c"
        }
        
        gradient = color_gradients.get(color_scheme, "#ffffb2, #fecc5c, #e31a1c")

        legend_html = f"""
        {{% macro html(this, kwargs) %}}
        <div style='
            position: fixed;
            bottom: 30px;
            left: 30px;
            width: 160px;
            z-index: 9999;
            font-size: 12px;
            background-color: white;
            padding: 10px;
            border: 2px solid grey;
            border-radius: 5px;
        '>
            <b>{title}</b><br>
            <div style='height: 10px; background: linear-gradient(to right, {gradient}); margin-top: 4px;'></div>
            <div style='display: flex; justify-content: space-between; margin-top: 4px;'>
                <span>{formatted_min}</span>
                <span>{formatted_max}</span>
            </div>
        </div>
        {{% endmacro %}}
        """

        legend = MacroElement()
        legend._template = Template(legend_html)
        map_obj.get_root().add_child(legend)


    def _generate_bins(self, min_val: float, max_val: float, num_bins: int = 5):
        """Generate clean rounded bins including full data range"""

        def round_down(val):
            if val >= 1_000_000:
                return int(val // 100_000 * 100_000)
            elif val >= 100_000:
                return int(val // 10_000 * 10_000)
            elif val >= 10_000:
                return int(val // 1_000 * 1_000)
            else:
                return int(val)

        def round_up(val):
            if val >= 1_000_000:
                return int((val + 100_000 - 1) // 100_000 * 100_000)
            elif val >= 100_000:
                return int((val + 10_000 - 1) // 10_000 * 10_000)
            elif val >= 10_000:
                return int((val + 1_000 - 1) // 1_000 * 1_000)
            else:
                return int(val)

        start = round_down(min_val)
        end = round_up(max_val)

        return list(np.linspace(start, end, num=num_bins))



    def _add_choropleth_layer(self, map_obj: folium.Map, gdf: gpd.GeoDataFrame, indicator_column: str):
        """Add choropleth layer for health indicators"""
        
        req_indicators = ['Total_living_with_HIV', 'Total_population']

        if indicator_column not in gdf.columns:
            st.warning(f"⚠️ Indicator '{indicator_column}' not available in current selection")
            return
        
        color_scheme = MAP_LAYERS.get(indicator_column, {}).get("color_scheme", "YlOrRd")
  
  
        def _format_legend_name(col_name: str) -> str:
            """Format the map scale based on the column name"""
            if col_name in req_indicators:
                return f"{col_name.replace('_', ' ').title()}"
            else:
                return col_name.replace('_', ' ').title()
        
        min_val = gdf[indicator_column].min()
        max_val = gdf[indicator_column].max()

        bins = self._generate_nice_bins(min_val, max_val, num_bins=6)

        choropleth_args = {
            "geo_data": gdf,
            "data": gdf,
            "columns": [gdf.index, indicator_column],
            "key_on": 'feature.id',
            "fill_color": color_scheme,
            "fill_opacity": 0.7,
            "line_opacity": 0.2,
            "legend_name": _format_legend_name(indicator_column),
            "highlight": True,
        }
         
        if indicator_column in req_indicators:
            bins = self._generate_bins(min_val, max_val, num_bins=5)
            choropleth_args["bins"] = bins
        
        folium.Choropleth(**choropleth_args).add_to(map_obj)

        legend_title = _format_legend_name(indicator_column)
        self._add_custom_legend(map_obj, legend_title, color_scheme, min_val, max_val, indicator_column)

        for idx, row in gdf.iterrows():
            area_name = self._get_area_name(row)
            indicator_value = row[indicator_column] if pd.notna(row[indicator_column]) else "N/A"
            
            formatted_value = self._format_display_number(indicator_value, indicator_column)
            
            folium.Marker(
                location=[row.geometry.centroid.y, row.geometry.centroid.x],
                popup=folium.Popup(
                    f"<b>{area_name}</b><br>{indicator_column}: {formatted_value}",
                    max_width=200
                ),
                icon=None
            ).add_to(map_obj)
    

    def _format_legend_number(self, value, indicator_column: str) -> str:
        """Format numbers in the legend for better readability and spacing"""

        if pd.isna(value):
            return "N/A"
        
        num_val = float(value)
        
        if indicator_column in ['Total_living_with_HIV', 'Total_population']:
            if num_val >= 1_000_000:
                rounded = round(num_val / 100_000) * 100_000
                return f"{rounded / 1_000_000:.1f}M"
            elif num_val >= 100_000:
                rounded = round(num_val / 10_000) * 10_000 
                return f"{rounded / 1_000:.0f}K"
            elif num_val >= 1_000:
                rounded = round(num_val / 1_000) * 1_000
                return f"{rounded / 1_000:.0f}K"
            else:
                return f"{int(num_val):,}"

        elif isinstance(num_val, float):
            return f"{num_val:.1f}"
        else:
            return str(num_val)
               
   
    def _format_display_number(self, value, indicator_column):
        """Format numbers for display in tooltips and metrics"""
        if pd.notna(value) and indicator_column in ['Total_living_with_HIV', 'Total_population']:
             num_value = int(value)
             if num_value >= 1_000_000:
                  return f"{num_value / 1_000_000:.1f}M"
             elif num_value >= 1_000:
                  return f"{num_value / 1_000:.1f}K"
             else:
                  return f"{num_value:,}"
        else:
            return str(value) if pd.notna(value) else "N/A"
    

    def _add_neighboring_context(self, map_obj: folium.Map, geographic_selection: Dict):
        """Add neighboring municipalities for context"""
        
        neighbors = self.spatial_queries.get_neighboring_municipalities(
            geographic_selection["municipality_code"],
            radius_km=MAP_CONFIG["neighboring_radius_km"]
        )
        
        if neighbors is not None and not neighbors.empty:
            folium.Choropleth(
                geo_data=neighbors,
                fill_color='Blues',
                fill_opacity=0.3,
                line_opacity=0.5,
                legend_name='Neighboring Areas'
            ).add_to(map_obj)
    
    def _get_area_name(self, row) -> str:
        """Get appropriate area name from row data"""
    
        name_columns = ["MUNICNAME_1", "DISTRICT_N", "Province_name", "CAT_B", "DISTRICT", "PROVINCE"]
        
        for col in name_columns:
            if col in row and pd.notna(row[col]):
                return str(row[col])
        
        return "Unknown Area"
    
    
    def _create_default_map(self) -> folium.Map:
        """Create default map when no data available"""
        
        m = folium.Map(
            location=self.default_center,
            zoom_start=self.default_zoom,
            tiles='OpenStreetMap'
        )
        
        folium.Marker(
            location=self.default_center,
            popup="South Africa - No data available for current selection",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)
        
        return m