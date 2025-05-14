import pandas as pd
import requests

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
    url = "https://www.dallasopendata.com/resource/qv6i-rri7.json"
    params = {
        "$limit": limit,
        "$order": "date_of_occurrence DESC"
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        data = pd.DataFrame(response.json())
        data = standardize_column_names(data)
        
        # Check if required columns exist
        required_columns = ['latitude', 'longitude', 'nibrs_crime_category', 'date_of_occurrence']
        missing_columns = [col for col in required_columns if col not in data.columns]
        
        if missing_columns:
            print(f"Warning: Missing required columns: {missing_columns}")
            print(f"Available columns: {data.columns.tolist()}")
            return pd.DataFrame()
        
        # Convert coordinates to numeric values
        data['latitude'] = pd.to_numeric(data['latitude'], errors='coerce')
        data['longitude'] = pd.to_numeric(data['longitude'], errors='coerce')
        
        # Convert date if it exists
        if 'date_of_occurrence' in data.columns:
            data['date_of_occurrence'] = pd.to_datetime(data['date_of_occurrence'], errors='coerce')
        
        # Drop rows with missing required data
        data = data.dropna(subset=['latitude', 'longitude'])
        
        return data
        
    except Exception as e:
        print(f"Error fetching crime data: {str(e)}")
        return pd.DataFrame()