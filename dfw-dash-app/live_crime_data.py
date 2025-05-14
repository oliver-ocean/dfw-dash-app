import pandas as pd
import requests
from datetime import datetime, timedelta

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
    Returns empty DataFrame with appropriate columns if fetch fails
    """
    url = "https://www.dallasopendata.com/resource/qv6i-rri7.json"
    
    # Calculate date range for last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    params = {
        "$limit": limit,
        "$where": f"date_of_occurrence >= '{start_date.strftime('%Y-%m-%d')}' AND date_of_occurrence <= '{end_date.strftime('%Y-%m-%d')}'",
        "$order": "date_of_occurrence DESC"
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        data = pd.DataFrame(response.json())
        if data.empty:
            print("Warning: No crime data returned from API")
            return create_empty_crime_df()
            
        data = standardize_column_names(data)
        
        # Check if required columns exist
        required_columns = ['latitude', 'longitude', 'nibrs_crime_category', 'date_of_occurrence']
        missing_columns = [col for col in required_columns if col not in data.columns]
        
        if missing_columns:
            print(f"Warning: Missing required crime data columns: {missing_columns}")
            print(f"Available columns: {data.columns.tolist()}")
            return create_empty_crime_df()
        
        # Convert coordinates to numeric values
        data['latitude'] = pd.to_numeric(data['latitude'], errors='coerce')
        data['longitude'] = pd.to_numeric(data['longitude'], errors='coerce')
        
        # Convert date if it exists
        if 'date_of_occurrence' in data.columns:
            data['date_of_occurrence'] = pd.to_datetime(data['date_of_occurrence'], errors='coerce')
        
        # Drop rows with missing required data
        data = data.dropna(subset=['latitude', 'longitude'])
        
        if data.empty:
            print("Warning: No valid crime data after cleaning")
            return create_empty_crime_df()
            
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching crime data: {str(e)}")
        return create_empty_crime_df()
    except Exception as e:
        print(f"Unexpected error processing crime data: {str(e)}")
        return create_empty_crime_df()

def create_empty_crime_df():
    """Create an empty DataFrame with the expected crime data structure"""
    return pd.DataFrame({
        'latitude': [],
        'longitude': [],
        'nibrs_crime_category': [],
        'date_of_occurrence': []
    })