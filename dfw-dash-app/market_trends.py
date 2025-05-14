import pandas as pd
import plotly.express as px
from dash import dcc

def load_mock_market_trends():
    months = pd.date_range(start='2023-01-01', periods=24, freq='M')
    data = []
    for month in months:
        data.append({
            'Month': month,
            'Metric': 'Rent',
            'Value': 1500 + (month.month - 1) * 30 + (month.year - 2023) * 100
        })
        data.append({
            'Month': month,
            'Metric': 'Lease Price/SqFt',
            'Value': 22 + (month.month - 1) * 0.5 + (month.year - 2023)
        })
        data.append({
            'Month': month,
            'Metric': 'Sale Price/SqFt',
            'Value': 180 + (month.month - 1) * 2 + (month.year - 2023) * 5
        })
    return pd.DataFrame(data)

def render_market_trends_chart():
    df = load_mock_market_trends()
    fig = px.line(df, x="Month", y="Value", color="Metric", title="2-Year Market Trends")
    return dcc.Graph(figure=fig)