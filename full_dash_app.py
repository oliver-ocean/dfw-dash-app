import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import pandas as pd
import numpy as np
from crime_plot import render_crime_chart

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

def get_color(scale_value: float, data_type: str) -> str:
    """Convert scale value (0-1) to color string based on data type"""
    if pd.isna(scale_value):
        return 'rgba(128, 128, 128, 0.1)'  # Very transparent gray for missing data
    
    if data_type == 'traffic':
        # For traffic: green (low) to red (high)
        r = int(255 * scale_value)
        g = int(255 * (1 - scale_value))
        opacity = 0.2 + (scale_value * 0.5)  # Opacity increases with value
        return f'rgba({r}, {g}, 0, {opacity})'
    else:  # crime
        # Red gradient with varying opacity
        opacity = 0.1 + (scale_value * 0.6)  # More transparent for low values
        return f'rgba(255, 0, 0, {opacity})'

def create_traffic_overlay():
    if traffic_grid.empty:
        return []
    
    rectangles = []
    for _, row in traffic_grid.iterrows():
        sw_corner, ne_corner = row['cell_bounds']
        color = get_color(row['color_scale'], 'traffic')
        rectangles.append(
            dl.Rectangle(
                bounds=[sw_corner, ne_corner],
                color='transparent',  # No border
                fillColor=color,
                weight=0,
                fillOpacity=1,  # We control opacity in the color itself
                children=[
                    dl.Tooltip(f"Traffic Level: {row['weighted_aadt']:,.0f} AADT")
                ]
            )
        )
    return rectangles

def create_crime_overlay():
    if crime_grid.empty:
        return []
    
    rectangles = []
    for _, row in crime_grid.iterrows():
        sw_corner, ne_corner = row['cell_bounds']
        color = get_color(row['color_scale'], 'crime')
        rectangles.append(
            dl.Rectangle(
                bounds=[sw_corner, ne_corner],
                color='transparent',  # No border
                fillColor=color,
                weight=0,
                fillOpacity=1,  # We control opacity in the color itself
                children=[
                    dl.Tooltip(f"Crime Density: {row['weighted_crime']:.2f}")
                ]
            )
        )
    return rectangles

# Map layers
traffic_layer = dl.LayerGroup(id="traffic-layer", children=create_traffic_overlay())
price_layer = dl.LayerGroup(id="price-layer")  # Placeholder for price markers
crime_layer = dl.LayerGroup(id="crime-layer", children=create_crime_overlay())

# Map
map_component = dl.Map(
    center=[32.78, -97.15],
    zoom=10,
    children=[
        dl.TileLayer(url='https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png'),
        traffic_layer,
        price_layer,
        crime_layer
    ],
    style={'width': '100%', 'height': '600px'},
    id="main-map"
)

# Legend
legend = html.Div([
    html.H6("Legend"),
    html.Div([
        html.Span("Traffic: ", style={'font-weight': 'bold'}),
        html.Span("Green (Low) → Red (High)")
    ]),
    html.Div([
        html.Span("Crime: ", style={'font-weight': 'bold'}),
        html.Span("Light Red (Low) → Dark Red (High)")
    ])
], style={'padding': '10px', 'background-color': 'white', 'border-radius': '5px'})

# Layer selector dropdown
layer_selector = dbc.Card([
    html.H5("Select Data Layer"),
    dcc.Dropdown(
        id="layer-toggle",
        options=[
            {"label": "Traffic Density", "value": "traffic"},
            {"label": "Property Values", "value": "price"},
            {"label": "Crime Density", "value": "crime"}
        ],
        value="traffic",
        clearable=False
    ),
], body=True)

# Tabs for charts
tabs = dcc.Tabs(id="charts-tabs", children=[
    dcc.Tab(label="Traffic Patterns", value="traffic"),
    dcc.Tab(label="Market Trends", value="market"),
    dcc.Tab(label="Crime Trends", value="crime")
], value="traffic")
charts_content = html.Div(id="charts-content")

# Store clicked location
clicked_location = dcc.Store(id='clicked-location', data={'lat': None, 'lon': None})

# Layout
app.layout = dbc.Container([
    clicked_location,
    dbc.Row([dbc.Col(layer_selector, width=12)]),
    dbc.Row([
        dbc.Col(map_component, width=9),
        dbc.Col(legend, width=3)
    ]),
    dbc.Row([dbc.Col([tabs, charts_content], width=12)])
], fluid=True)

@app.callback(
    Output("traffic-layer", "children"),
    Output("price-layer", "children"),
    Output("crime-layer", "children"),
    Input("layer-toggle", "value")
)
def toggle_map_layers(selected):
    traffic = create_traffic_overlay() if selected == "traffic" else []
    price = [] if selected == "price" else []  # Placeholder for price markers
    crime = create_crime_overlay() if selected == "crime" else []
    return traffic, price, crime

@app.callback(
    Output('clicked-location', 'data'),
    Input('main-map', 'click_latLng')
)
def store_clicked_location(click_latLng):
    if click_latLng is None:
        return {'lat': None, 'lon': None}
    return {'lat': click_latLng[0], 'lon': click_latLng[1]}

@app.callback(
    Output("charts-content", "children"),
    Input("charts-tabs", "value"),
    Input("clicked-location", "data"),
    Input("layer-toggle", "value")
)
def update_charts(tab, clicked_location, active_layer):
    ctx = dash.callback_context
    if not ctx.triggered:
        return "No data selected"
    
    lat = clicked_location.get('lat')
    lon = clicked_location.get('lon')
    
    if tab == "traffic" and active_layer == "traffic":
        return render_traffic_chart(clicked_lat=lat, clicked_lon=lon)
    elif tab == "market" and active_layer == "price":
        return render_market_trends_chart()
    elif tab == "crime" and active_layer == "crime":
        return render_crime_chart(clicked_lat=lat, clicked_lon=lon)
    else:
        return "Please select a location on the map and ensure the corresponding layer is active" 