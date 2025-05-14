import dash
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import dash_leaflet as dl

from traffic_plot import render_traffic_chart
from market_trends import render_market_trends_chart
from crime_map import render_crime_markers

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

traffic_layer = dl.LayerGroup(id="traffic-layer")
price_layer = dl.LayerGroup(id="price-layer")
crime_layer = dl.LayerGroup(id="crime-layer")

map_component = dl.Map(center=[32.9, -97.0], zoom=9, children=[
    dl.TileLayer(),
    traffic_layer,
    price_layer,
    crime_layer
], style={'width': '100%', 'height': '600px'}, id="main-map")

toggle_controls = dbc.Card([
    html.H5("Toggle Layers & Views"),
    dbc.Checklist(
        options=[
            {"label": "Traffic", "value": "traffic"},
            {"label": "Price & Lease", "value": "price"},
            {"label": "Crime", "value": "crime"}
        ],
        value=["traffic", "price"],
        id="layer-toggle",
        inline=True
    ),
], body=True)

tabs = dcc.Tabs(id="charts-tabs", value="traffic", children=[
    dcc.Tab(label="Traffic Patterns", value="traffic"),
    dcc.Tab(label="Market Trends", value="market")
])

charts_content = html.Div(id="charts-content")

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(toggle_controls, width=12)
    ]),
    dbc.Row([
        dbc.Col(map_component, width=12)
    ]),
    dbc.Row([
        dbc.Col([tabs, charts_content], width=12)
    ])
], fluid=True)

@app.callback(
    Output("traffic-layer", "children"),
    Output("price-layer", "children"),
    Output("crime-layer", "children"),
    Input("layer-toggle", "value")
)
def toggle_map_layers(selected):
    traffic = [dl.Marker(position=[32.9, -97.0], children=dl.Tooltip("Traffic Marker"))] if "traffic" in selected else []
    price = [dl.Marker(position=[32.8, -97.1], children=dl.Tooltip("Lease Marker"))] if "price" in selected else []
    crime = render_crime_markers() if "crime" in selected else []
    return traffic, price, crime

@app.callback(
    Output("charts-content", "children"),
    Input("charts-tabs", "value")
)
def update_chart(tab):
    if tab == "traffic":
        return render_traffic_chart()
    return render_market_trends_chart()

if __name__ == "__main__":
    app.run(debug=True)