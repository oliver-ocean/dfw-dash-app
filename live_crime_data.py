import pandas as pd
import requests
from datetime import datetime, timedelta
import numpy as np
from urllib.parse import quote, urlencode

def convert_state_plane_to_latlong(x, y):
    """Convert Texas State Plane coordinates to lat/long
    Approximate conversion for Dallas coordinates"""
    if pd.isna(x) or pd.isna(y):
        return None, None
    try:
        x = float(x)
        y = float(y)
        
        # These are approximate conversion factors for the Dallas area
        # For more accuracy, we should use a proper coordinate transformation library
        lat = y  # Default to using coordinates as-is
        lon = x
        
        # Check if these are state plane coordinates (they'll be very large numbers)
        if abs(x) > 10000:
            # Convert from feet to degrees (approximate for Dallas area)
            lat = 32.7767 + (y - 6961650) / 364320  # 1 degree ≈ 364320 feet at this latitude
            lon = -96.7970 + (x - 2475470) / 288360  # 1 degree ≈ 288360 feet at this longitude
        
        # Validate the conversion result
        if not (32.4 <= lat <= 33.2 and -97.7 <= lon <= -96.3):
            if abs(x) > 10000:
                print(f"Invalid conversion result: ({lat}, {lon}) from ({x}, {y})")
            return None, None
            
        return lat, lon
    except Exception as e:
        print(f"Error converting coordinates: {str(e)}")
        return None, None

def standardize_crime_category(category):
    """Standardize crime categories between Dallas and Fort Worth"""
    if pd.isna(category):
        return "OTHER"
    
    category = str(category).upper()
    
    if "THEFT" in category or "BURGLARY" in category or "ROBBERY" in category:
        return "THEFT"
    elif "ASSAULT" in category or "VIOLENCE" in category:
        return "ASSAULT"
    elif "MURDER" in category or "HOMICIDE" in category:
        return "HOMICIDE"
    elif "RAPE" in category or "SEXUAL" in category:
        return "SEXUAL ASSAULT"
    elif "AUTO" in category or "VEHICLE" in category:
        return "AUTO THEFT"
    elif "DRUG" in category or "NARCOTIC" in category:
        return "DRUG OFFENSE"
    else:
        return "OTHER"

def create_mock_crime_data():
    """Create mock crime data for testing when API calls fail"""
    # Create a date range for the last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    dates = pd.date_range(start=start_date, end=end_date, freq='H')
    
    # Create mock data
    n_records = 100
    mock_data = pd.DataFrame({
        'date_of_occurrence': np.random.choice(dates, n_records),
        'latitude': np.random.uniform(32.65, 33.00, n_records),  # DFW area
        'longitude': np.random.uniform(-97.00, -96.70, n_records),
        'nibrs_crime_category': np.random.choice(['THEFT', 'ASSAULT', 'BURGLARY'], n_records),
        'city': np.random.choice(['Dallas', 'Fort Worth'], n_records)
    })
    
    return mock_data

def fetch_crime_data(limit=1000):
    """
    Fetch crime data from both Dallas and Fort Worth Open Data Portals
    Returns mock data if both fetches fail
    """
    all_data = []
    
    # Calculate the date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    thirty_days_ago = start_date.strftime('%Y-%m-%dT00:00:00.000')
    
    print(f"Fetching crime data from {thirty_days_ago} to present")
    
    # Try to fetch Dallas crime data
    dallas_url = "https://www.dallasopendata.com/resource/qv6i-rri7.json"
    try:
        dallas_params = {
            "$limit": str(limit),
            "$where": f"date1 >= '{thirty_days_ago}'",
            "$order": "date1 DESC",
            "$select": "date1 as date_of_occurrence, y_cordinate, x_coordinate, nibrs_crime_category"
        }
        
        headers = {
            "Accept": "application/json"
        }
        
        # Use requests with properly encoded parameters
        response = requests.get(
            dallas_url,
            params=dallas_params,
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"Dallas API Error: {response.status_code}")
            print(f"Response content: {response.text}")
            raise Exception(f"API returned status code {response.status_code}")
            
        dallas_data = pd.DataFrame(response.json())
        if not dallas_data.empty:
            print(f"Successfully fetched Dallas crime data: {len(dallas_data)} records")
            
            # Convert coordinates
            print("\nProcessing Dallas coordinates...")
            coords = []
            for _, row in dallas_data.iterrows():
                try:
                    x = float(row['x_coordinate']) if pd.notna(row['x_coordinate']) else None
                    y = float(row['y_cordinate']) if pd.notna(row['y_cordinate']) else None
                    if x is not None and y is not None:
                        lat, lon = convert_state_plane_to_latlong(x, y)
                        coords.append((lat, lon))
                    else:
                        coords.append((None, None))
                except Exception as e:
                    print(f"Error processing coordinates ({x}, {y}): {str(e)}")
                    coords.append((None, None))
            
            dallas_data['latitude'] = [lat for lat, _ in coords]
            dallas_data['longitude'] = [lon for _, lon in coords]
            
            valid_coords = dallas_data[dallas_data['latitude'].notna()]
            print(f"Successfully converted {len(valid_coords)} coordinates")
            if len(valid_coords) > 0:
                print("\nSample of converted coordinates:")
                sample = valid_coords.sample(min(5, len(valid_coords)))
                for _, row in sample.iterrows():
                    print(f"  ({row['latitude']:.6f}, {row['longitude']:.6f})")
            
            # Add city and clean up
            dallas_data['city'] = 'Dallas'
            dallas_data = dallas_data.drop(['x_coordinate', 'y_cordinate'], axis=1)
            all_data.append(dallas_data)
        else:
            print("Dallas API returned empty dataset")
            
    except Exception as e:
        print(f"Error fetching Dallas crime data: {str(e)}")
        print(f"Failed URL: {response.url if 'response' in locals() else dallas_url}")

    # Try to fetch Fort Worth crime data
    fw_url = "https://data.fortworthtexas.gov/resource/k6ic-7kp7.json"
    try:
        fw_params = {
            "$limit": str(limit),
            "$where": f"from_date >= '{thirty_days_ago}'",
            "$order": "from_date DESC",
            "$select": "from_date as date_of_occurrence, location_1, offense_desc as nibrs_crime_category"
        }
        
        headers = {
            "Accept": "application/json"
        }
        
        # Use requests with properly encoded parameters
        response = requests.get(
            fw_url,
            params=fw_params,
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"Fort Worth API Error: {response.status_code}")
            print(f"Response content: {response.text}")
            raise Exception(f"API returned status code {response.status_code}")
            
        fw_data = pd.DataFrame(response.json())
        if not fw_data.empty:
            print(f"Successfully fetched Fort Worth crime data: {len(fw_data)} records")
            fw_data['city'] = 'Fort Worth'
            
            # Extract latitude and longitude from location_1 field
            if 'location_1' in fw_data.columns:
                try:
                    fw_data['latitude'] = fw_data['location_1'].apply(lambda x: float(x['latitude']) if isinstance(x, dict) and 'latitude' in x else None)
                    fw_data['longitude'] = fw_data['location_1'].apply(lambda x: float(x['longitude']) if isinstance(x, dict) and 'longitude' in x else None)
                    print(f"Extracted coordinates for {len(fw_data[fw_data['latitude'].notna()])} records")
                except Exception as e:
                    print(f"Error extracting coordinates from location_1: {str(e)}")
            
            # Drop the location_1 column as we've extracted what we need
            fw_data = fw_data.drop(['location_1'], axis=1, errors='ignore')
            all_data.append(fw_data)
        else:
            print("Fort Worth API returned empty dataset")
            
    except Exception as e:
        print(f"Error fetching Fort Worth crime data: {str(e)}")
        print(f"Failed URL: {response.url if 'response' in locals() else fw_url}")

    # Combine data or use mock if both fail
    if not all_data:
        print("No real crime data available, using mock data")
        return create_mock_crime_data()
    
    # Combine all data
    data = pd.concat(all_data, ignore_index=True)
    print(f"\nCombined {len(data)} total records")
    
    # Check if required columns exist
    required_columns = ['latitude', 'longitude', 'date_of_occurrence']
    missing_required = [col for col in required_columns if col not in data.columns]
    if missing_required:
        print(f"Warning: Missing required crime data columns: {missing_required}")
        print(f"Available columns: {data.columns.tolist()}")
        return create_mock_crime_data()
    
    # Convert coordinates to numeric values
    data['latitude'] = pd.to_numeric(data['latitude'], errors='coerce')
    data['longitude'] = pd.to_numeric(data['longitude'], errors='coerce')
    
    # Convert and filter date if the column exists
    data['date_of_occurrence'] = pd.to_datetime(data['date_of_occurrence'], errors='coerce')
    data = data[data['date_of_occurrence'] >= start_date]
    
    print(f"After date filtering: {len(data)} records")
    
    # Standardize crime categories
    data['nibrs_crime_category'] = data['nibrs_crime_category'].apply(standardize_crime_category)
    
    # Drop any rows with missing coordinates or dates
    data = data.dropna(subset=['latitude', 'longitude', 'date_of_occurrence'])
    print(f"After dropping null values: {len(data)} records")
    
    # Print coordinate ranges before filtering
    print("\nCoordinate ranges before filtering:")
    print(f"Latitude range: {data['latitude'].min():.6f} to {data['latitude'].max():.6f}")
    print(f"Longitude range: {data['longitude'].min():.6f} to {data['longitude'].max():.6f}")
    
    # Filter out obviously invalid coordinates
    valid_coords = (
        (data['latitude'] >= 32.4) & (data['latitude'] <= 33.2) &  # DFW area bounds
        (data['longitude'] >= -97.7) & (data['longitude'] <= -96.3)  # Wider bounds to catch suburbs
    )
    
    data = data[valid_coords]
    
    if len(data) > 0:
        print("\nCoordinate ranges after filtering:")
        print(f"Latitude range: {data['latitude'].min():.6f} to {data['latitude'].max():.6f}")
        print(f"Longitude range: {data['longitude'].min():.6f} to {data['longitude'].max():.6f}")
        print(f"\nSample of valid coordinates:")
        sample = data.sample(min(5, len(data)))
        for _, row in sample.iterrows():
            print(f"  {row['city']}: ({row['latitude']:.6f}, {row['longitude']:.6f})")
    
    print(f"After coordinate validation: {len(data)} records")
    
    if len(data) == 0:
        print("No valid crime data after filtering, using mock data")
        return create_mock_crime_data()
    
    # Keep only the columns we need
    final_columns = ['date_of_occurrence', 'latitude', 'longitude', 'nibrs_crime_category', 'city']
    data = data[final_columns]
    
    print(f"Final dataset contains {len(data)} valid records")
    return data 