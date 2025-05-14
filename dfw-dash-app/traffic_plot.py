import pandas as pd
import plotly.express as px
from dash import dcc
from live_traffic_data import fetch_traffic_data

def render_traffic_chart():
    df = fetch_traffic_data()
    if df.empty or 'AADT' not in df:
        return dcc.Graph(figure=px.scatter(title="No traffic data available"))

    # Aggregate AADT by Road Name
    df = df.dropna(subset=['AADT', 'Road Name'])
    top_roads = df.groupby('Road Name')['AADT'].mean().sort_values(ascending=False).head(10).reset_index()
    fig = px.bar(top_roads, x='Road Name', y='AADT',
                 title='Top 10 Dallas Roads by Average Annual Daily Traffic',
                 labels={'AADT': 'AADT Volume'})
    return dcc.Graph(figure=fig)