import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc
from live_traffic_data import fetch_traffic_data
from data_processing import calculate_traffic_trends

def render_traffic_chart():
    df = fetch_traffic_data()
    if df.empty:
        return dcc.Graph(figure=px.scatter(title="No traffic data available"))

    # Calculate traffic trends
    trend_df = calculate_traffic_trends(df)
    if trend_df.empty:
        return dcc.Graph(figure=px.scatter(title="No traffic trend data available"))

    # Get year columns
    year_cols = [col for col in trend_df.columns if col.startswith('year_')]
    year_cols.sort()

    # Create line plot for each location
    fig = go.Figure()

    # Add a trace for each location
    for _, row in trend_df.iterrows():
        fig.add_trace(go.Scatter(
            x=list(range(1, len(year_cols) + 1)),
            y=[row[col] for col in year_cols],
            name=row['Road Name'],
            mode='lines+markers',
            hovertemplate=(
                "Road: %{text}<br>" +
                "Year: %{x}<br>" +
                "AADT: %{y:,.0f}<br>"
            ),
            text=[row['Road Name']] * len(year_cols)
        ))

    # Update layout
    fig.update_layout(
        title='Historical Traffic Trends by Location (Weighted Average)',
        xaxis_title='Years Back',
        yaxis_title='Weighted AADT',
        showlegend=True,
        legend_title='Road Names',
        hovermode='closest'
    )

    return dcc.Graph(figure=fig)