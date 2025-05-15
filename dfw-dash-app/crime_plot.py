import pandas as pd
import plotly.graph_objects as go
from dash import dcc
from live_crime_data import fetch_crime_data
import numpy as np
from datetime import datetime, timedelta

def render_crime_chart(clicked_lat=None, clicked_lon=None):
    """Render crime trends chart for the clicked location"""
    df = fetch_crime_data()
    if df.empty:
        return dcc.Graph(figure=go.Figure().add_annotation(
            text="No crime data available",
            showarrow=False,
            xref="paper",
            yref="paper"
        ))

    # If no location is clicked, show a message
    if clicked_lat is None or clicked_lon is None:
        return dcc.Graph(figure=go.Figure().add_annotation(
            text="Click a location on the map to see crime trends",
            showarrow=False,
            xref="paper",
            yref="paper"
        ))

    # Calculate distance to clicked point
    df['distance'] = np.sqrt(
        (df['latitude'] - clicked_lat)**2 + 
        (df['longitude'] - clicked_lon)**2
    )

    # Get crimes within 0.02 degrees (roughly 2km)
    nearby_crimes = df[df['distance'] < 0.02].copy()
    
    if nearby_crimes.empty:
        return dcc.Graph(figure=go.Figure().add_annotation(
            text="No crimes reported near this location",
            showarrow=False,
            xref="paper",
            yref="paper"
        ))

    # Create daily crime counts
    nearby_crimes['date'] = pd.to_datetime(nearby_crimes['date_of_occurrence']).dt.date
    daily_counts = nearby_crimes.groupby('date').size().reset_index(name='count')
    daily_counts['date'] = pd.to_datetime(daily_counts['date'])
    
    # Fill in missing dates with zeros
    date_range = pd.date_range(
        start=daily_counts['date'].min(),
        end=daily_counts['date'].max(),
        freq='D'
    )
    daily_counts = daily_counts.set_index('date').reindex(date_range, fill_value=0)
    daily_counts = daily_counts.reset_index()
    daily_counts.columns = ['date', 'count']

    # Calculate 7-day moving average
    daily_counts['7_day_avg'] = daily_counts['count'].rolling(window=7, min_periods=1).mean()

    # Create the plot
    fig = go.Figure()

    # Add the trend line
    fig.add_trace(go.Scatter(
        x=daily_counts['date'],
        y=daily_counts['7_day_avg'],
        mode='lines',
        name='7-day Moving Average',
        line=dict(color='red', width=2),
        hovertemplate=(
            "Date: %{x}<br>" +
            "Average Daily Crimes: %{y:.1f}<br>"
        )
    ))

    # Update layout
    fig.update_layout(
        title=f'Crime Trends (Past 30 Days)',
        xaxis_title='Date',
        yaxis_title='Number of Crimes',
        showlegend=True,
        hovermode='x unified'
    )

    return dcc.Graph(figure=fig) 