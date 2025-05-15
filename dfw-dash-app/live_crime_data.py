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
    Fetch crime data from both Dallas and Fort Worth Open Data Portals
    Returns mock data if both fetches fail
    """
    all_data = []
    
    # Try to fetch Dallas crime data
    dallas_url = "https://www.dallasopendata.com/resource/qv6i-rri7.json"
    try:
        dallas_params = {
            "$limit": limit,
            "$order": "date_of_occurrence DESC"
        }
        
        response = requests.get(dallas_url, params=dallas_params, timeout=10)
        response.raise_for_status()
        
        dallas_data = pd.DataFrame(response.json())
        if not dallas_data.empty:
            print("Successfully fetched Dallas crime data")
            dallas_data['city'] = 'Dallas'
            all_data.append(dallas_data)
    except Exception as e:
        print(f"Error fetching Dallas crime data: {str(e)}")

    # Try to fetch Fort Worth crime data
    fw_url = "https://data.fortworthtexas.gov/resource/k6ic-7kp7.json"
    try:
        fw_params = {
            "$limit": limit,
            "$order": "date_time DESC",
            "$where": "date_time > '" + (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%S') + "'"
        }
        
        response = requests.get(fw_url, params=fw_params, timeout=10)
        response.raise_for_status()
        
        fw_data = pd.DataFrame(response.json())
        if not fw_data.empty:
            print("Successfully fetched Fort Worth crime data")
            fw_data['city'] = 'Fort Worth'
            # Rename columns to match standardized format
            fw_data = fw_data.rename(columns={
                'latitude': 'y_coord',
                'longitude': 'x_coord',
                'date_time': 'date_of_occurrence',
                'crime_type': 'nibrs_crime_category'
            })
            all_data.append(fw_data)
    except Exception as e:
        print(f"Error fetching Fort Worth crime data: {str(e)}")

    # Combine data or use mock if both fail
    if not all_data:
        print("No real crime data available, using mock data")
        return create_mock_crime_data()
    
    # Combine all data
    data = pd.concat(all_data, ignore_index=True)
    data = standardize_column_names(data)
    
    # Check if required columns exist
    required_columns = ['latitude', 'longitude']
    missing_required = [col for col in required_columns if col not in data.columns]
    if missing_required:
        print(f"Warning: Missing required crime data columns: {missing_required}")
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

def create_mock_crime_data(n_points=100, city='both'):
    """Create mock crime data for testing and fallback"""
    # Define the DFW area bounds
    if city == 'Dallas':
        lat_min, lat_max = 32.65, 32.95
        lon_min, lon_max = -96.95, -96.7
    elif city == 'Fort Worth':
        lat_min, lat_max = 32.65, 32.95
        lon_min, lon_max = -97.45, -97.25
    else:  # both cities
        lat_min, lat_max = 32.65, 32.95
        lon_min, lon_max = -97.45, -96.7
    
    # Generate random data
    np.random.seed(42)  # For reproducibility
    
    # Generate dates for the last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    dates = [start_date + timedelta(days=x) for x in range(31)]
    
    # Define crime categories with weights
    crime_categories = {
        'THEFT': 0.3,
        'BURGLARY': 0.15,
        'ASSAULT': 0.2,
        'VANDALISM': 0.1,
        'AUTO THEFT': 0.15,
        'ROBBERY': 0.05,
        'OTHER': 0.05
    }
    
    # Create crime incidents
    data = []
    for _ in range(n_points):
        # Create clusters around major areas
        if np.random.random() < 0.7:  # 70% of points in clusters
            # Define major areas (lat, lon, radius)
            if city == 'Dallas' or city == 'both':
                major_areas = [
                    (32.78, -96.8, 0.05),  # Downtown Dallas
                    (32.85, -96.75, 0.03),  # North Dallas
                ]
            elif city == 'Fort Worth':
                major_areas = [
                    (32.75, -97.33, 0.05),  # Downtown Fort Worth
                    (32.72, -97.28, 0.03),  # South Fort Worth
                ]
            else:
                major_areas = [
                    (32.78, -96.8, 0.05),   # Downtown Dallas
                    (32.75, -97.33, 0.05),  # Downtown Fort Worth
                ]
            
            # Select a random major area
            center_lat, center_lon, radius = major_areas[np.random.randint(len(major_areas))]
            lat = np.random.normal(center_lat, radius)
            lon = np.random.normal(center_lon, radius)
        else:
            # Random points within bounds
            lat = np.random.uniform(lat_min, lat_max)
            lon = np.random.uniform(lon_min, lon_max)
        
        # Ensure coordinates are within bounds
        lat = np.clip(lat, lat_min, lat_max)
        lon = np.clip(lon, lon_min, lon_max)
        
        data.append({
            'latitude': lat,
            'longitude': lon,
            'date_of_occurrence': np.random.choice(dates),
            'nibrs_crime_category': np.random.choice(
                list(crime_categories.keys()),
                p=list(crime_categories.values())
            )
        })
    
    return pd.DataFrame(data)