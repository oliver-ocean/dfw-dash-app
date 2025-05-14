import dash
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import pandas as pd

from traffic_plot import render_traffic_chart
from market_trends import render_market_trends_chart
from live_crime_data import fetch_crime_data
from live_traffic_data import fetch_traffic_data

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Fetch live data
crime_df = fetch_crime_data()
traffic_df = fetch_traffic_data()

# Create marker layers from live data
def create_crime_markers():
    if crime_df.empty:
        return []
    
    markers = []
    for _, row in crime_df.iterrows():
        tooltip_text = ""
        if 'nibrs_crime_category' in row and pd.notna(row['nibrs_crime_category']):
            tooltip_text += str(row['nibrs_crime_category'])
        if 'date_of_occurrence' in row and pd.notna(row['date_of_occurrence']):
            if tooltip_text:
                tooltip_text += " "
            tooltip_text += f"({str(row['date_of_occurrence'])[:10]})"
        
        if not tooltip_text:
            tooltip_text = "Crime Incident"
            
        markers.append(
            dl.Marker(
                position=[row['latitude'], row['longitude']],
                children=dl.Tooltip(tooltip_text)
            )
        )
    return markers

def create_traffic_markers():
    if traffic_df.empty:
        return []
    
    markers = []
    for _, row in traffic_df.iterrows():
        if pd.notna(row.get('Latitude')) and pd.notna(row.get('Longitude')):
            tooltip_text = ""
            if 'Road Name' in row and pd.notna(row['Road Name']):
                tooltip_text += str(row['Road Name'])
            if 'AADT' in row and pd.notna(row['AADT']):
                if tooltip_text:
                    tooltip_text += " — "
                tooltip_text += f"AADT: {row['AADT']}"
            
            if not tooltip_text:
                tooltip_text = "Traffic Point"
                
            markers.append(
                dl.CircleMarker(
                    center=[row['Latitude'], row['Longitude']],
                    radius=5,
                    color='red',
                    fillOpacity=0.7,
                    children=dl.Tooltip(tooltip_text)
                )
            )
    return markers

# Map layers
traffic_layer = dl.LayerGroup(id="traffic-layer", children=create_traffic_markers())
price_layer = dl.LayerGroup(id="price-layer")  # Placeholder for price markers
crime_layer = dl.LayerGroup(id="crime-layer", children=create_crime_markers())

# Map
map_component = dl.Map(center=[32.9, -97.0], zoom=9, children=[
    dl.TileLayer(),
    traffic_layer,
    price_layer,
    crime_layer
], style={'width': '100%', 'height': '600px'}, id="main-map")

# Toggle controls
toggle_controls = dbc.Card([
    html.H5("Toggle Layers & Views"),
    dbc.Checklist(
        options=[
            {"label": "Traffic", "value": "traffic"},
            {"label": "Price & Lease", "value": "price"},
            {"label": "Crime", "value": "crime"}
        ],
        value=["traffic", "price", "crime"],
        id="layer-toggle",
        inline=True
    ),
], body=True)

# Tabs for charts
tabs = dcc.Tabs(id="charts-tabs", value="traffic", children=[
    dcc.Tab(label="Traffic Patterns", value="traffic"),
    dcc.Tab(label="Market Trends", value="market")
])
charts_content = html.Div(id="charts-content")

# Layout
app.layout = dbc.Container([
    dbc.Row([dbc.Col(toggle_controls, width=12)]),
    dbc.Row([dbc.Col(map_component, width=12)]),
    dbc.Row([dbc.Col([tabs, charts_content], width=12)])
], fluid=True)

@app.callback(
    Output("traffic-layer", "children"),
    Output("price-layer", "children"),
    Output("crime-layer", "children"),
    Input("layer-toggle", "value")
)
def toggle_map_layers(selected):
    traffic = create_traffic_markers() if "traffic" in selected else []
    price = [dl.Marker(position=[32.8, -97.1], children=dl.Tooltip("Lease Marker"))] if "price" in selected else []
    crime = create_crime_markers() if "crime" in selected else []
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
    import os
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port, debug=False)