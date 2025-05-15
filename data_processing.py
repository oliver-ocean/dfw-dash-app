def calculate_weighted_traffic(df: pd.DataFrame, grid_size: int = 100) -> pd.DataFrame:
    """
    Calculate weighted traffic values for a grid of points covering the map area.
    Uses inverse distance weighting for interpolation with log transformation.
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
    
    # Apply log transformation for better color distribution
    result['log_aadt'] = np.log1p(result['weighted_aadt'])  # log1p to handle zeros
    min_log_aadt = result['log_aadt'].min()
    max_log_aadt = result['log_aadt'].max()
    result['color_scale'] = (result['log_aadt'] - min_log_aadt) / (max_log_aadt - min_log_aadt)
    
    return result 