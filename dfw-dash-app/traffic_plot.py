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

    # If a location is clicked, filter for nearby points
    if clicked_lat is not None and clicked_lon is not None:
        # Calculate distances to clicked point
        distances = np.sqrt(
            (trend_df['Latitude'] - clicked_lat)**2 + 
            (trend_df['Longitude'] - clicked_lon)**2
        )
        # Use stronger distance decay for weighting (distance^4)
        weights = 1 / (distances**4 + 1e-10)
        weights = weights / weights.sum()
        
        # Sort by distance and take top 5 closest points
        trend_df['distance'] = distances
        trend_df['weight'] = weights
        trend_df = trend_df.nsmallest(5, 'distance')

    # Get year columns
    year_cols = [col for col in trend_df.columns if col.startswith('year_')]
    year_cols.sort()

    # Create line plot
    fig = go.Figure()

    # Add a trace for each location
    for _, row in trend_df.iterrows():
        weight = row.get('weight', 1.0)  # Default weight of 1.0 if no click
        opacity = min(1.0, weight * 5)  # Scale opacity by weight, max at 1.0
        
        fig.add_trace(go.Scatter(
            x=list(range(1, len(year_cols) + 1)),
            y=[row[col] for col in year_cols],
            name=row['Road Name'],
            mode='lines+markers',
            opacity=opacity,
            hovertemplate=(
                "Road: %{text}<br>" +
                "Year: %{x}<br>" +
                "AADT: %{y:,.0f}<br>"
            ),
            text=[row['Road Name']] * len(year_cols)
        ))

    # Update layout
    title = 'Historical Traffic Trends'
    if clicked_lat is not None:
        title += ' (Nearby Selected Location)'
    
    fig.update_layout(
        title=title,
        xaxis_title='Years Back',
        yaxis_title='AADT',
        showlegend=True,
        legend_title='Road Names',
        hovermode='closest'
    )

    return dcc.Graph(figure=fig)