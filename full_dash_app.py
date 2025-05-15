import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import dash_leaflet as dl
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from map_layer import CrimeMapLayer, create_crime_layer
from traffic_layer import TrafficMapLayer, create_traffic_layer
from crime_visualization import CrimeVisualization
from crime_plot import render_crime_chart
from traffic_plot import render_traffic_chart

# Initialize the app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Initialize visualization systems
crime_viz = CrimeVisualization(grid_size=50)
crime_layer = CrimeMapLayer(resolution=50)
traffic_layer = TrafficMapLayer(resolution=50)

# Update data on startup
crime_layer.update_data()
traffic_layer.update_data()

# Map layers
base_layer = dl.TileLayer(
    url='https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png',
    attribution='&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>, &copy; <a href="https://carto.com/attributions">CARTO</a>'
)

crime_heatmap = create_crime_layer()
traffic_heatmap = create_traffic_layer()

# Layer control options
overlay_layers = {
    'Crime Heatmap': crime_heatmap,
    'Traffic Heatmap': traffic_heatmap
}

# Map
map_component = dl.Map(
    center=[32.78, -96.8],  # Dallas center
    zoom=11,
    children=[
        base_layer,
        dl.LayerGroup(id="heatmap-layers", children=[crime_heatmap, traffic_heatmap]),
        dl.LayerControl(overlays=overlay_layers, position="topright")
    ],
    style={'width': '100%', 'height': '70vh'},
    id="main-map"
)

# Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("DFW Area Analysis", className="text-center mb-4"),
            dbc.ButtonGroup([
                dbc.Button("Crime Data", id="show-crime", n_clicks=0, color="danger", className="me-1"),
                dbc.Button("Traffic Data", id="show-traffic", n_clicks=0, color="warning", className="me-1")
            ], className="mb-3"),
            html.Div([
                map_component,
                html.Div(
                    "Click anywhere on the map to see detailed statistics",
                    className="text-muted text-center mt-2"
                )
            ], className="mb-4"),
        ], width=12)
    ]),
    dbc.Row([
        dbc.Col([
            html.Div(id="analysis-content")
        ], width=12)
    ])
], fluid=True)

# Callbacks
@app.callback(
    Output("heatmap-layers", "children"),
    [Input("show-crime", "n_clicks"),
     Input("show-traffic", "n_clicks")]
)
def update_visible_layers(crime_clicks, traffic_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        # Default to showing crime layer
        return [crime_heatmap]
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if button_id == "show-crime":
        return [crime_heatmap]
    elif button_id == "show-traffic":
        return [traffic_heatmap]
    return []

@app.callback(
    Output("analysis-content", "children"),
    [Input("main-map", "click_lat_lng"),
     Input("show-crime", "n_clicks"),
     Input("show-traffic", "n_clicks")]
)
def update_analysis(click_lat_lng, crime_clicks, traffic_clicks):
    if click_lat_lng is None:
        return html.Div("Click a location on the map to see detailed analysis")
    
    ctx = dash.callback_context
    if not ctx.triggered:
        return html.Div("Select a data type and click on the map")
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    lat, lon = click_lat_lng
    
    if button_id == "show-crime" or (button_id == "main-map" and crime_clicks > traffic_clicks):
        return render_crime_chart(lat, lon)
    elif button_id == "show-traffic" or (button_id == "main-map" and traffic_clicks > crime_clicks):
        return render_traffic_chart(lat, lon)
    
    return html.Div("Select a data type to view analysis")

if __name__ == '__main__':
    app.run_server(debug=True) 