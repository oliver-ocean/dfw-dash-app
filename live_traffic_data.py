import requests
import pandas as pd
from io import StringIO

def fetch_traffic_data():
    url = "https://gis-txdot.opendata.arcgis.com/datasets/d5f56ecd2b274b4d8dc3c2d6fe067d37_0.csv"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        
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
            return pd.DataFrame()
        
        # Filter for Dallas and Tarrant counties and print counts
        if 'County_Name' in df.columns:
            print("Total records before filtering:", len(df))
            dallas_mask = df['County_Name'].str.contains('Dallas', case=False, na=False)
            tarrant_mask = df['County_Name'].str.contains('Tarrant', case=False, na=False)
            df = df[dallas_mask | tarrant_mask]
            print("Records after county filtering:", len(df))
            print("Dallas County records:", sum(dallas_mask))
            print("Tarrant County records:", sum(tarrant_mask))
        
        # Convert coordinates to numeric, handling potential string formats
        for col in ['Latitude', 'Longitude']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Print coordinate ranges for debugging
        print("Latitude range:", df['Latitude'].min(), "to", df['Latitude'].max())
        print("Longitude range:", df['Longitude'].min(), "to", df['Longitude'].max())
        
        # Drop rows with missing required data
        df = df.dropna(subset=['Road Name', 'AADT', 'Latitude', 'Longitude'])
        print("Final record count after cleaning:", len(df))
        
        return df
    except Exception as e:
        print(f"Error fetching traffic data: {str(e)}")
        return pd.DataFrame() 