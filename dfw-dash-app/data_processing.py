import pandas as pd
import numpy as np
from scipy.spatial.distance import cdist
from typing import List, Tuple, Dict

def calculate_weighted_traffic(df: pd.DataFrame, grid_size: int = 50) -> pd.DataFrame:
    """
    Calculate weighted traffic values for a grid of points covering the map area.
    Uses inverse distance weighting for interpolation with percentile-based color scaling.
    """
    if df.empty:
        return pd.DataFrame()

    # Create a grid of points
    lat_min, lat_max = df['Latitude'].min(), df['Latitude'].max()
    lon_min, lon_max = df['Longitude'].min(), df['Longitude'].max()
    
    lat_grid = np.linspace(lat_min, lat_max, grid_size)
    lon_grid = np.linspace(lon_min, lon_max, grid_size)
    grid_points = np.array([(lat, lon) for lat in lat_grid for lon in lon_grid])
    
    # Get data points
    data_points = df[['Latitude', 'Longitude']].values
    aadt_values = df['AADT'].values
    
    # Calculate distances between grid points and data points
    distances = cdist(grid_points, data_points)
    
    # Calculate weights with stronger distance decay (using distance^4)
    weights = 1 / (distances ** 4 + 1e-10)  # Add small constant to avoid division by zero
    weights = weights / weights.sum(axis=1, keepdims=True)
    
    # Calculate weighted AADT for each grid point
    weighted_aadt = np.dot(weights, aadt_values)
    
    # Create result DataFrame
    result = pd.DataFrame({
        'Latitude': grid_points[:, 0],
        'Longitude': grid_points[:, 1],
        'weighted_aadt': weighted_aadt
    })
    
    # Calculate percentile ranks for color scaling
    result['color_scale'] = result['weighted_aadt'].rank(pct=True)
    
    return result

def calculate_weighted_crime(df: pd.DataFrame, grid_size: int = 50) -> pd.DataFrame:
    """
    Calculate weighted crime density for a grid of points covering the map area.
    Uses inverse distance weighting for interpolation with percentile-based color scaling.
    """
    if df.empty:
        return pd.DataFrame()

    # Create a grid of points
    lat_min, lat_max = df['latitude'].min(), df['latitude'].max()
    lon_min, lon_max = df['longitude'].min(), df['longitude'].max()
    
    lat_grid = np.linspace(lat_min, lat_max, grid_size)
    lon_grid = np.linspace(lon_min, lon_max, grid_size)
    grid_points = np.array([(lat, lon) for lat in lat_grid for lon in lon_grid])
    
    # Count crimes at each location
    crime_counts = df.groupby(['latitude', 'longitude']).size().reset_index(name='count')
    crime_points = crime_counts[['latitude', 'longitude']].values
    crime_values = crime_counts['count'].values
    
    # Calculate distances between grid points and crime points
    distances = cdist(grid_points, crime_points)
    
    # Calculate weights with stronger distance decay (using distance^4)
    weights = 1 / (distances ** 4 + 1e-10)  # Add small constant to avoid division by zero
    weights = weights / weights.sum(axis=1, keepdims=True)
    
    # Calculate weighted crime density for each grid point
    weighted_crime = np.dot(weights, crime_values)
    
    # Create result DataFrame
    result = pd.DataFrame({
        'Latitude': grid_points[:, 0],
        'Longitude': grid_points[:, 1],
        'weighted_crime': weighted_crime
    })
    
    # Calculate percentile ranks for color scaling
    result['color_scale'] = result['weighted_crime'].rank(pct=True)
    
    return result

def calculate_traffic_trends(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate traffic trends using historical AADT data
    """
    if df.empty:
        return pd.DataFrame()
        
    # Get all AADT history columns
    hist_cols = [col for col in df.columns if col.startswith('AADT_RPT_HIST_') and col.endswith('_QTY')]
    hist_cols.sort()  # Sort to ensure chronological order
    
    # Create a list to store trend data
    trend_data = []
    
    # Process each location
    for _, row in df.iterrows():
        location_data = {
            'Latitude': row['Latitude'],
            'Longitude': row['Longitude'],
            'Road Name': row.get('Road Name', 'Unknown Road')
        }
        
        # Get historical values
        historical_values = [row[col] for col in hist_cols]
        
        # Calculate weighted average of nearby points for each time period
        nearby_points = df[
            (abs(df['Latitude'] - row['Latitude']) < 0.01) &
            (abs(df['Longitude'] - row['Longitude']) < 0.01)
        ]
        
        weighted_history = []
        for col in hist_cols:
            nearby_values = nearby_points[col].dropna()
            if not nearby_values.empty:
                distances = np.sqrt(
                    (nearby_points['Latitude'] - row['Latitude'])**2 +
                    (nearby_points['Longitude'] - row['Longitude'])**2
                )
                weights = 1 / (distances + 1e-10)
                weights = weights / weights.sum()
                weighted_avg = (nearby_values * weights).sum()
                weighted_history.append(weighted_avg)
            else:
                weighted_history.append(row[col])
        
        # Add to trend data
        location_data.update({
            f'year_{i+1}': val
            for i, val in enumerate(weighted_history)
        })
        trend_data.append(location_data)
    
    return pd.DataFrame(trend_data)

def calculate_crime_trends(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate crime trends over time
    """
    if df.empty:
        return pd.DataFrame()
    
    # Convert date to datetime if not already
    df['date_of_occurrence'] = pd.to_datetime(df['date_of_occurrence'])
    
    # Group by location and month
    df['month'] = df['date_of_occurrence'].dt.to_period('M')
    crime_trends = df.groupby(['latitude', 'longitude', 'month']).size().reset_index(name='count')
    
    # Pivot to get time series format
    crime_trends = crime_trends.pivot_table(
        index=['latitude', 'longitude'],
        columns='month',
        values='count',
        fill_value=0
    ).reset_index()
    
    return crime_trends 