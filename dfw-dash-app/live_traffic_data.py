import pandas as pd
import requests
from io import StringIO

def standardize_column_names(df):
    """Standardize column names based on common variations"""
    column_mapping = {
        # County name variations
        'County_Name': ['CNTY_NM', 'COUNTY_NAME', 'COUNTY', 'CountyName', 'County_Name'],
        # Road name variations
        'Road Name': ['Road Name', 'ROAD_NAME', 'RD_NAME', 'ROADNAME', 'STREET_NAME'],
        # Traffic count variations
        'AADT': ['AADT', 'AVG_DAILY_TRAFFIC', 'TRAFFIC_COUNT', 'DailyTraffic'],
        # Location variations
        'Latitude': ['Latitude', 'LAT', 'LATITUDE', 'Y'],
        'Longitude': ['Longitude', 'LONG', 'LON', 'LONGITUDE', 'X']
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
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        df = pd.read_csv(StringIO(response.text))
        df = standardize_column_names(df)
        
        # Check if required columns exist
        required_columns = ['County_Name', 'Road Name', 'AADT', 'Latitude', 'Longitude']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"Warning: Missing required columns: {missing_columns}")
            print(f"Available columns: {df.columns.tolist()}")
            return pd.DataFrame()
        
        # Filter for Dallas county if county column exists
        if 'County_Name' in df.columns:
            df = df[df['County_Name'].str.contains('Dallas', case=False, na=False)]
        
        # Convert coordinates to numeric, handling potential string formats
        for col in ['Latitude', 'Longitude']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Drop rows with missing required data
        df = df.dropna(subset=['Road Name', 'AADT', 'Latitude', 'Longitude'])
        
        return df
    except Exception as e:
        print(f"Error fetching traffic data: {str(e)}")
        return pd.DataFrame()