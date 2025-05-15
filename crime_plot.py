import pandas as pd
import plotly.graph_objects as go
from dash import dcc
from crime_stats_db import CrimeStatsDB
import numpy as np
from datetime import datetime, timedelta

def render_crime_chart(clicked_lat=None, clicked_lon=None, radius_km: float = 2.0):
    """
    Render crime trends chart for the clicked location using pre-computed statistics
    
    Parameters:
    -----------
    clicked_lat : float
        Latitude of clicked point
    clicked_lon : float
        Longitude of clicked point
    radius_km : float
        Radius in kilometers to analyze
    """
    # Initialize stats database
    stats_db = CrimeStatsDB()
    
    # If no location is clicked, show a message
    if clicked_lat is None or clicked_lon is None:
        return dcc.Graph(figure=go.Figure().add_annotation(
            text="Click a location on the map to see crime trends and risk analysis",
            showarrow=False,
            xref="paper",
            yref="paper"
        ))

    # Get location statistics
    stats = stats_db.get_location_stats(
        clicked_lat,
        clicked_lon,
        radius=radius_km / 111.0  # Convert km to degrees
    )
    
    if not stats:
        return dcc.Graph(figure=go.Figure().add_annotation(
            text="No crime data available for this location",
            showarrow=False,
            xref="paper",
            yref="paper"
        ))
    
    # Create figure with subplots
    fig = go.Figure()
    
    # Add time series of crime counts
    monthly_trend = stats['monthly_trend']
    
    # Plot total crime count trend
    fig.add_trace(go.Scatter(
        x=[m['month'] for m in monthly_trend],
        y=[m['crime_count'] for m in monthly_trend],
        mode='lines+markers',
        name='Total Crimes',
        line=dict(color='red', width=2)
    ))
    
    # Plot crime categories
    for category in ['violent_count', 'property_count', 'other_count']:
        fig.add_trace(go.Scatter(
            x=[m['month'] for m in monthly_trend],
            y=[m[category] for m in monthly_trend],
            mode='lines',
            name=category.replace('_count', '').title(),
            line=dict(dash='dash', width=1)
        ))
    
    # Add bar chart for recent crime type breakdown
    recent_stats = stats['recent_stats']
    fig.add_trace(go.Bar(
        x=['Total', 'Violent', 'Property', 'Other'],
        y=[
            recent_stats['total'],
            recent_stats['violent'],
            recent_stats['property'],
            recent_stats['other']
        ],
        name='Recent Average',
        yaxis='y2',
        marker_color='rgba(255,0,0,0.7)'
    ))
    
    # Update layout
    fig.update_layout(
        title=f'Crime Analysis (Risk Score: {stats["current_risk"]:.3f})',
        xaxis=dict(title='Date'),
        yaxis=dict(title='Crime Count'),
        yaxis2=dict(
            title='Recent Average (3 months)',
            overlaying='y',
            side='right'
        ),
        showlegend=True,
        height=600,
        hovermode='x unified'
    )
    
    # Add annotations with statistics
    fig.add_annotation(
        text=(f"Risk Score: {stats['current_risk']:.3f}\n"
              f"Recent Total: {recent_stats['total']:.1f}\n"
              f"Recent Violent: {recent_stats['violent']:.1f}\n"
              f"Recent Property: {recent_stats['property']:.1f}"),
        xref="paper",
        yref="paper",
        x=0.02,
        y=0.98,
        showarrow=False,
        font=dict(size=12),
        align="left",
        bgcolor="rgba(255,255,255,0.8)"
    )
    
    return dcc.Graph(figure=fig)

def create_heatmap(resolution: int = 100):
    """
    Create a crime risk heatmap using pre-computed statistics
    
    Parameters:
    -----------
    resolution : int
        Number of points in each dimension for the heatmap
    """
    # Initialize stats database
    stats_db = CrimeStatsDB(grid_size=resolution)
    
    # Get current heatmap data
    points = stats_db.get_current_heatmap_data()
    
    if points.empty:
        return go.Figure()
    
    # Create heatmap
    fig = go.Figure(data=go.Densitymapbox(
        lat=points['latitude'],
        lon=points['longitude'],
        z=points['risk_score'],
        radius=20,
        colorscale='Reds',
        zmin=0,
        zmax=1
    ))
    
    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox=dict(
            center=dict(
                lat=points['latitude'].mean(),
                lon=points['longitude'].mean()
            ),
            zoom=10
        ),
        title='Crime Risk Heatmap',
        height=800
    )
    
    return fig

def test_plotting():
    """Test the plotting functionality"""
    print("Testing crime chart rendering...")
    test_lat, test_lon = 32.78, -96.8  # Downtown Dallas
    chart = render_crime_chart(test_lat, test_lon)
    print("Crime chart created successfully")
    
    print("\nTesting heatmap creation...")
    heatmap = create_heatmap(resolution=50)  # Lower resolution for testing
    print("Heatmap created successfully")

if __name__ == "__main__":
    test_plotting() 