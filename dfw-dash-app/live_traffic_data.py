import pandas as pd
import requests
from io import StringIO
import numpy as np

def standardize_column_names(df):
    """Standardize column names based on common variations"""
    column_mapping = {
        # County name variations
        'County_Name': ['CNTY_NM', 'COUNTY_NAME', 'COUNTY', 'CountyName', 'County_Name'],
        # Road name variations
        'Road Name': ['Road Name', 'ROAD_NAME', 'RD_NAME', 'ROADNAME', 'STREET_NAME', 'ON_ROAD'],
        # Traffic count variations
        'AADT': ['AADT', 'AVG_DAILY_TRAFFIC', 'TRAFFIC_COUNT', 'DailyTraffic', 'AADT_RPT_QTY'],
        # Location variations
        'Latitude': ['Latitude', 'LAT', 'LATITUDE', 'Y', 'y'],
        'Longitude': ['Longitude', 'LONG', 'LON', 'LONGITUDE', 'X', 'x']
    }
    
    # Create a mapping of actual columns to standardized names
    rename_dict = {}
    for standard_name, variations in column_mapping.items():
        for variant in variations:
            if variant in df.columns:
                rename_dict[variant] = standard_name
                break
    
    # Rename columns if matches found
    if rename_dict:
        df = df.rename(columns=rename_dict)
    
    return df

def fetch_traffic_data():
    url = "https://gis-txdot.opendata.arcgis.com/datasets/d5f56ecd2b274b4d8dc3c2d6fe067d37_0.csv"
    try:
        response = requests.get(url, timeout=10)  # Add timeout
        response.raise_for_status()
        
        df = pd.read_csv(StringIO(response.text))
        
        # Print available columns for debugging
        print("Available columns before standardization:", df.columns.tolist())
        
        df = standardize_column_names(df)
        
        # Print standardized columns for debugging
        print("Available columns after standardization:", df.columns.tolist())
        
        # Check if required columns exist
        required_columns = ['County_Name', 'Road Name', 'AADT', 'Latitude', 'Longitude']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"Warning: Missing required columns: {missing_columns}")
            print(f"Available columns: {df.columns.tolist()}")
            return create_mock_traffic_data()  # Return mock data instead of empty DataFrame
        
        # Filter for Dallas and Tarrant counties
        if 'County_Name' in df.columns:
            dallas_mask = df['County_Name'].str.contains('Dallas', case=False, na=False)
            tarrant_mask = df['County_Name'].str.contains('Tarrant', case=False, na=False)
            df = df[dallas_mask | tarrant_mask]
        
        # Convert coordinates to numeric, handling potential string formats
        for col in ['Latitude', 'Longitude']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Drop rows with missing required data
        df = df.dropna(subset=['Road Name', 'AADT', 'Latitude', 'Longitude'])
        
        if len(df) == 0:
            print("No valid data after filtering, using mock data")
            return create_mock_traffic_data()
            
        return df
    except Exception as e:
        print(f"Error fetching traffic data: {str(e)}")
        return create_mock_traffic_data()

def create_mock_traffic_data(n_points=50):
    """Create mock traffic data for testing and fallback"""
    # Define the DFW area bounds
    lat_min, lat_max = 32.6, 33.0
    lon_min, lon_max = -97.2, -96.8
    
    # Generate random data
    np.random.seed(42)  # For reproducibility
    df = pd.DataFrame({
        'County_Name': np.random.choice(['Dallas', 'Tarrant'], n_points),
        'Road Name': [f'Road {i}' for i in range(n_points)],
        'AADT': np.random.randint(5000, 150000, n_points),
        'Latitude': np.random.uniform(lat_min, lat_max, n_points),
        'Longitude': np.random.uniform(lon_min, lon_max, n_points)
    })
    
    # Add some historical data for trends
    for year in range(1, 6):
        variation = np.random.normal(1, 0.1, n_points)
        df[f'AADT_RPT_HIST_{year}_QTY'] = df['AADT'] * variation
    
    return df