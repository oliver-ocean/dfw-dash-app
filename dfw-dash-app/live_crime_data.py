import pandas as pd
import requests
from datetime import datetime, timedelta
import numpy as np

def standardize_column_names(df):
    """Standardize column names based on common variations"""
    column_mapping = {
        # Location variations
        'latitude': ['latitude', 'lat', 'y_coord', 'y'],
        'longitude': ['longitude', 'long', 'lon', 'x_coord', 'x'],
        # Crime category variations
        'nibrs_crime_category': ['nibrs_crime_category', 'crime_category', 'offense_category', 'crime_type'],
        # Date variations
        'date_of_occurrence': ['date_of_occurrence', 'incident_date', 'offense_date', 'date']
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

def fetch_crime_data(limit=100):
    """
    Fetch crime data from Dallas Open Data Portal
    Returns mock data if fetch fails
    """
    url = "https://www.dallasopendata.com/resource/qv6i-rri7.json"
    
    try:
        params = {
            "$limit": limit,
            "$order": "date_of_occurrence DESC"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = pd.DataFrame(response.json())
        if data.empty:
            print("Warning: No crime data returned from API")
            return create_mock_crime_data()
            
        data = standardize_column_names(data)
        
        # Check if required columns exist
        required_columns = ['latitude', 'longitude']
        missing_required = [col for col in required_columns if col not in data.columns]
        if missing_required:
            print(f"Warning: Missing required crime data columns: {missing_required}")
            print(f"Available columns: {data.columns.tolist()}")
            return create_mock_crime_data()
        
        # Convert coordinates to numeric values
        data['latitude'] = pd.to_numeric(data['latitude'], errors='coerce')
        data['longitude'] = pd.to_numeric(data['longitude'], errors='coerce')
        
        # Convert and filter date if the column exists
        if 'date_of_occurrence' in data.columns:
            data['date_of_occurrence'] = pd.to_datetime(data['date_of_occurrence'], errors='coerce')
            cutoff_date = datetime.now() - timedelta(days=30)
            data = data[data['date_of_occurrence'] >= cutoff_date]
        
        # Drop any rows with missing coordinates
        data = data.dropna(subset=['latitude', 'longitude'])
        
        if len(data) == 0:
            print("No valid crime data after filtering, using mock data")
            return create_mock_crime_data()
            
        return data
    except Exception as e:
        print(f"Error fetching crime data: {str(e)}")
        return create_mock_crime_data()

def create_mock_crime_data(n_points=100):
    """Create mock crime data for testing and fallback"""
    # Define the Dallas area bounds
    lat_min, lat_max = 32.65, 32.95
    lon_min, lon_max = -96.95, -96.7
    
    # Generate random data
    np.random.seed(42)  # For reproducibility
    
    # Generate dates for the last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    dates = [start_date + timedelta(days=x) for x in range(31)]
    
    # Create crime incidents
    data = []
    for _ in range(n_points):
        data.append({
            'latitude': np.random.uniform(lat_min, lat_max),
            'longitude': np.random.uniform(lon_min, lon_max),
            'date_of_occurrence': np.random.choice(dates),
            'nibrs_crime_category': np.random.choice([
                'THEFT', 'BURGLARY', 'ASSAULT', 'VANDALISM',
                'AUTO THEFT', 'ROBBERY', 'OTHER'
            ])
        })
    
    return pd.DataFrame(data)