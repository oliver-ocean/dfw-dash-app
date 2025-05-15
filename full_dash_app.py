import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import dash_leaflet as dl
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from map_layer import CrimeMapLayer
from crime_visualization import CrimeVisualization

# Initialize the app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Initialize visualization systems
crime_viz = CrimeVisualization(grid_size=50)
crime_layer = CrimeMapLayer(resolution=50)

# Update crime data on startup
crime_layer.update_data()

def create_crime_markers():
    """Create crime visualization markers"""
    return crime_layer.get_heatmap_data()

def create_crime_chart(lat, lon):
    """Create crime trend chart for location"""
    analysis = crime_layer.get_trend_analysis(lat, lon)
    if not analysis:
        return go.Figure()
        
    trend_data = analysis['trend']
    fig = go.Figure()
    
    # Add trend line
    fig.add_trace(go.Scatter(
        x=[d['month'] for d in trend_data],
        y=[d['risk_score'] for d in trend_data],
        name='Risk Score',
        line=dict(color='red')
    ))
    
    # Update layout
    fig.update_layout(
        title='Crime Risk Trend',
        xaxis_title='Month',
        yaxis_title='Risk Score',
        template='plotly_white'
    )
    
    return fig

# Map layers
traffic_layer = dl.LayerGroup(id="traffic-layer", children=create_traffic_markers())
price_layer = dl.LayerGroup(id="price-layer")  # Placeholder for price markers
crime_layer = dl.LayerGroup(id="crime-layer", children=create_crime_markers())

# Map
map_component = dl.Map(
    center=[32.78, -97.15],
    zoom=10,
    children=[
        dl.TileLayer(),
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
        html.Span("Green = Low, Red = High")
    ]),
    html.Div([
        html.Span("Crime: ", style={'font-weight': 'bold'}),
        html.Span("Blue = Low, Red = High")
    ])
], style={'padding': '10px', 'background-color': 'white', 'border-radius': '5px'})

# Toggle controls
toggle_controls = dbc.Card([
    html.H5("Select Data Layer"),
    dbc.RadioItems(
        options=[
            {"label": "Traffic", "value": "traffic"},
            {"label": "Price & Lease", "value": "price"},
            {"label": "Crime", "value": "crime"}
        ],
        value="traffic",
        id="layer-toggle",
        inline=True
    ),
], body=True)

# Tabs for charts
tabs = dcc.Tabs(id="charts-tabs", value="traffic", children=[
    dcc.Tab(label="Traffic Patterns", value="traffic"),
    dcc.Tab(label="Market Trends", value="market"),
    dcc.Tab(label="Crime Analysis", value="crime")
])
charts_content = html.Div(id="charts-content")

# Store clicked location
clicked_location = dcc.Store(id='clicked-location', data={'lat': None, 'lon': None})

# Layout
app.layout = dbc.Container([
    clicked_location,
    dbc.Row([dbc.Col(toggle_controls, width=12)]),
    dbc.Row([
        dbc.Col(map_component, width=9),
        dbc.Col(legend, width=3)
    ]),
    dbc.Row([dbc.Col([tabs, charts_content], width=12)])
], fluid=True)

# Callbacks
@app.callback(
    Output("charts-content", "children"),
    [Input("charts-tabs", "value"),
     Input("clicked-location", "data")]
)
def update_charts(tab, location):
    if not location or location['lat'] is None:
        return html.Div("Click a location on the map to see detailed analysis")
        
    if tab == "crime":
        fig = create_crime_chart(location['lat'], location['lon'])
        return dcc.Graph(figure=fig)
    elif tab == "traffic":
        # Your existing traffic chart logic
        return html.Div("Traffic analysis coming soon")
    else:
        # Your existing market chart logic
        return html.Div("Market analysis coming soon")

@app.callback(
    Output("clicked-location", "data"),
    [Input("main-map", "click_lat_lng")]
)
def store_clicked_location(click_lat_lng):
    if click_lat_lng is None:
        return {'lat': None, 'lon': None}
    return {'lat': click_lat_lng[0], 'lon': click_lat_lng[1]}

if __name__ == '__main__':
    app.run_server(debug=True) 