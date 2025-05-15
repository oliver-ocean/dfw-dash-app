import pandas as pd
import numpy as np
from scipy.spatial.distance import cdist
from typing import List, Tuple, Dict

def calculate_weighted_traffic(df: pd.DataFrame, grid_size: int = 50) -> pd.DataFrame:
    """
    Calculate weighted traffic values for a grid of points covering the map area.
    Uses inverse distance weighting for interpolation with percentile-based color scaling.
    Returns grid cells for rectangle overlays.
    """
    if df.empty:
        return pd.DataFrame()

    # Create a grid of points with cell boundaries
    lat_min, lat_max = df['Latitude'].min(), df['Latitude'].max()
    lon_min, lon_max = df['Longitude'].min(), df['Longitude'].max()
    
    # Add buffer to ensure coverage
    lat_buffer = (lat_max - lat_min) * 0.05
    lon_buffer = (lon_max - lon_min) * 0.05
    lat_min -= lat_buffer
    lat_max += lat_buffer
    lon_min -= lon_buffer
    lon_max += lon_buffer
    
    lat_step = (lat_max - lat_min) / grid_size
    lon_step = (lon_max - lon_min) / grid_size
    
    # Create grid cells with boundaries
    grid_cells = []
    for i in range(grid_size):
        for j in range(grid_size):
            cell = {
                'cell_bounds': [
                    [lat_min + i * lat_step, lon_min + j * lon_step],  # SW corner
                    [lat_min + (i + 1) * lat_step, lon_min + (j + 1) * lon_step]  # NE corner
                ],
                'center_lat': lat_min + (i + 0.5) * lat_step,
                'center_lon': lon_min + (j + 0.5) * lon_step
            }
            grid_cells.append(cell)
    
    # Convert to DataFrame for processing
    grid_df = pd.DataFrame(grid_cells)
    
    # Get data points
    data_points = df[['Latitude', 'Longitude']].values
    aadt_values = df['AADT'].values
    
    # Calculate distances between grid centers and data points
    grid_centers = grid_df[['center_lat', 'center_lon']].values
    distances = cdist(grid_centers, data_points)
    
    # Calculate weights with stronger distance decay (using distance^4)
    weights = 1 / (distances ** 4 + 1e-10)
    weights = weights / weights.sum(axis=1, keepdims=True)
    
    # Calculate weighted AADT for each grid cell
    grid_df['weighted_aadt'] = np.dot(weights, aadt_values)
    
    # Calculate percentile ranks for color scaling
    grid_df['color_scale'] = grid_df['weighted_aadt'].rank(pct=True)
    
    return grid_df

def calculate_weighted_crime(df: pd.DataFrame, grid_size: int = 30) -> pd.DataFrame:
    """
    Calculate weighted crime density for a grid of points covering the map area.
    Uses inverse distance weighting for interpolation with percentile-based color scaling.
    Returns grid cells for rectangle overlays.
    """
    if df.empty:
        return pd.DataFrame()

    # Create a grid of points with cell boundaries
    lat_min, lat_max = df['latitude'].min(), df['latitude'].max()
    lon_min, lon_max = df['longitude'].min(), df['longitude'].max()
    
    # Add buffer to ensure coverage
    lat_buffer = (lat_max - lat_min) * 0.05
    lon_buffer = (lon_max - lon_min) * 0.05
    lat_min -= lat_buffer
    lat_max += lat_buffer
    lon_min -= lon_buffer
    lon_max += lon_buffer
    
    lat_step = (lat_max - lat_min) / grid_size
    lon_step = (lon_max - lon_min) / grid_size
    
    # Create grid cells with boundaries
    grid_cells = []
    for i in range(grid_size):
        for j in range(grid_size):
            cell = {
                'cell_bounds': [
                    [lat_min + i * lat_step, lon_min + j * lon_step],  # SW corner
                    [lat_min + (i + 1) * lat_step, lon_min + (j + 1) * lon_step]  # NE corner
                ],
                'center_lat': lat_min + (i + 0.5) * lat_step,
                'center_lon': lon_min + (j + 0.5) * lon_step
            }
            grid_cells.append(cell)
    
    # Convert to DataFrame for processing
    grid_df = pd.DataFrame(grid_cells)
    
    # Count crimes at each location with time weighting
    df['days_ago'] = (pd.Timestamp.now() - pd.to_datetime(df['date_of_occurrence'])).dt.days
    df['time_weight'] = np.exp(-df['days_ago'] / 365)  # Exponential decay over a year
    
    crime_counts = df.groupby(['latitude', 'longitude']).agg({
        'time_weight': 'sum'
    }).reset_index()
    
    crime_points = crime_counts[['latitude', 'longitude']].values
    crime_values = crime_counts['time_weight'].values
    
    # Calculate distances between grid centers and crime points
    grid_centers = grid_df[['center_lat', 'center_lon']].values
    distances = cdist(grid_centers, crime_points)
    
    # Calculate weights with stronger distance decay (using distance^3 for better performance)
    weights = 1 / (distances ** 3 + 1e-10)
    weights = weights / weights.sum(axis=1, keepdims=True)
    
    # Calculate weighted crime density for each grid cell
    grid_df['weighted_crime'] = np.dot(weights, crime_values)
    
    # Calculate percentile ranks for color scaling
    grid_df['color_scale'] = grid_df['weighted_crime'].rank(pct=True)
    
    return grid_df

def calculate_weighted_traffic(df: pd.DataFrame, grid_size: int = 100) -> pd.DataFrame:
    """
    Calculate weighted traffic values for a grid of points covering the map area.
    Uses inverse distance weighting for interpolation with double log transformation.
    """
    if df.empty:
        return pd.DataFrame()

    # Create a grid of points
    lat_min, lat_max = df['Latitude'].min(), df['Latitude'].max()
    lon_min, lon_max = df['Longitude'].min(), df['Longitude'].max()
    
    # Add a small buffer to ensure coverage
    lat_buffer = (lat_max - lat_min) * 0.05
    lon_buffer = (lon_max - lon_min) * 0.05
    lat_min -= lat_buffer
    lat_max += lat_buffer
    lon_min -= lon_buffer
    lon_max += lon_buffer
    
    lat_grid = np.linspace(lat_min, lat_max, grid_size)
    lon_grid = np.linspace(lon_min, lon_max, grid_size)
    grid_points = np.array([(lat, lon) for lat in lat_grid for lon in lon_grid])
    
    # Get data points
    data_points = df[['Latitude', 'Longitude']].values
    aadt_values = df['AADT'].values
    
    # Calculate distances between grid points and data points
    distances = cdist(grid_points, data_points)
    
    # Calculate weights (inverse distance weighting)
    weights = 1 / (distances ** 2 + 1e-10)  # Add small constant to avoid division by zero
    weights = weights / weights.sum(axis=1, keepdims=True)
    
    # Calculate weighted AADT for each grid point
    weighted_aadt = np.dot(weights, aadt_values)
    
    # Create result DataFrame
    result = pd.DataFrame({
        'Latitude': grid_points[:, 0],
        'Longitude': grid_points[:, 1],
        'weighted_aadt': weighted_aadt
    })
    
    # Apply double log transformation for better color distribution
    # First log transformation
    result['log1_aadt'] = np.log1p(result['weighted_aadt'])
    # Second log transformation on the normalized first log
    min_log1 = result['log1_aadt'].min()
    max_log1 = result['log1_aadt'].max()
    normalized_log1 = (result['log1_aadt'] - min_log1) / (max_log1 - min_log1)
    result['log2_aadt'] = np.log1p(normalized_log1 * 100)  # Scale up before second log
    
    # Calculate final color scale
    min_log2 = result['log2_aadt'].min()
    max_log2 = result['log2_aadt'].max()
    result['color_scale'] = (result['log2_aadt'] - min_log2) / (max_log2 - min_log2)
    
    return result 