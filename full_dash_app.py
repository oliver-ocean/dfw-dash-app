import dash
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import pandas as pd
import numpy as np

from traffic_plot import render_traffic_chart
from market_trends import render_market_trends_chart
from live_crime_data import fetch_crime_data
from live_traffic_data import fetch_traffic_data
from data_processing import calculate_weighted_traffic, calculate_weighted_crime

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Fetch live data
crime_df = fetch_crime_data()
traffic_df = fetch_traffic_data()

# Process data for visualization
traffic_grid = calculate_weighted_traffic(traffic_df)
crime_grid = calculate_weighted_crime(crime_df)

# Map
map_component = dl.Map(center=[32.78, -97.15], zoom=10, children=[
    dl.TileLayer(),
    traffic_layer,
    price_layer,
    crime_layer
], style={'width': '100%', 'height': '600px'}, id="main-map")

def create_traffic_markers():
    if traffic_grid.empty:
        return []
    
    markers = []
    for _, row in traffic_grid.iterrows():
        markers.append(
            dl.CircleMarker(
                center=[row['Latitude'], row['Longitude']],
                radius=4,  # Smaller radius
                color=get_color(row['color_scale']),
                fillOpacity=0.4,  # More transparent
                weight=1,
                children=dl.Tooltip(f"Traffic Level: {row['weighted_aadt']:,.0f} AADT")
            )
        )
    return markers

def create_crime_markers():
    if crime_grid.empty:
        return []
    
    markers = []
    for _, row in crime_grid.iterrows():
        markers.append(
            dl.CircleMarker(
                center=[row['Latitude'], row['Longitude']],
                radius=4,  # Smaller radius
                color=get_crime_color(row['color_scale']),
                fillOpacity=0.4,  # More transparent
                weight=1,
                children=dl.Tooltip(f"Crime Density: {row['weighted_crime']:.2f}")
            )
        )
    return markers 