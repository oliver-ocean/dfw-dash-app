import pandas as pd
import plotly.express as px
import dash
from dash import html, dcc, Input, Output

def load_mock_hourly_traffic():
    roads = ['I-35', 'US-75', 'Loop 12']
    hours = list(range(7, 23))
    data = []
    for road in roads:
        for hour in hours:
            data.append({
                'Road': road,
                'Hour': f"{hour}:00",
                'TrafficVolume': 10000 + (hour - 7) * 1200 + (road == 'US-75') * 1000
            })
    return pd.DataFrame(data)

def render_traffic_chart():
    df = load_mock_hourly_traffic()
    fig = px.line(df, x="Hour", y="TrafficVolume", color="Road",
                  title="Hourly Traffic Volume by Road (Mock Data)")
    return dcc.Graph(figure=fig)