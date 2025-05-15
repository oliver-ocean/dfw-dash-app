import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc
from live_traffic_data import fetch_traffic_data
from data_processing import calculate_traffic_trends
import numpy as np

def render_traffic_chart(clicked_lat=None, clicked_lon=None):
    df = fetch_traffic_data()
    if df.empty:
        return dcc.Graph(figure=px.scatter(title="No traffic data available"))

    # Calculate traffic trends
    trend_df = calculate_traffic_trends(df)
    if trend_df.empty:
        return dcc.Graph(figure=px.scatter(title="No traffic trend data available"))

    # If no location is clicked, show a message
    if clicked_lat is None or clicked_lon is None:
        return dcc.Graph(figure=go.Figure().add_annotation(
            text="Click a location on the map to see traffic trends",
            showarrow=False,
            xref="paper",
            yref="paper"
        ))

    # Calculate distances to clicked point
    distances = np.sqrt(
        (trend_df['Latitude'] - clicked_lat)**2 + 
        (trend_df['Longitude'] - clicked_lon)**2
    )
    
    # Get the nearest point
    nearest_idx = distances.argmin()
    nearest_point = trend_df.iloc[nearest_idx]

    # Get year columns
    year_cols = [col for col in trend_df.columns if col.startswith('year_')]
    year_cols.sort()

    # Create line plot
    fig = go.Figure()

    # Add a trace for the nearest location
    fig.add_trace(go.Scatter(
        x=list(range(1, len(year_cols) + 1)),
        y=[nearest_point[col] for col in year_cols],
        name=nearest_point['Road Name'],
        mode='lines+markers',
        line=dict(color='blue', width=2),
        hovertemplate=(
            "Road: %{text}<br>" +
            "Year: %{x}<br>" +
            "AADT: %{y:,.0f}<br>"
        ),
        text=[nearest_point['Road Name']] * len(year_cols)
    ))

    # Update layout
    title = f'Historical Traffic Trends for {nearest_point["Road Name"]}'
    
    fig.update_layout(
        title=title,
        xaxis_title='Years Back',
        yaxis_title='AADT',
        showlegend=True,
        hovermode='x unified'
    )

    return dcc.Graph(figure=fig)