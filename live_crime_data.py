def fetch_crime_data(limit=1000):
    """
    Fetch crime data from both Dallas and Fort Worth Open Data Portals
    Returns mock data if both fetches fail
    """
    all_data = []
    
    # Try to fetch Dallas crime data
    dallas_url = "https://www.dallasopendata.com/resource/qv6i-rri7.json"
    try:
        # Get data from the last 30 days
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%S')
        dallas_params = {
            "$limit": limit,
            "$where": f"date_of_occurrence > '{thirty_days_ago}'",
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
        # Get data from the last 30 days
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%S')
        fw_params = {
            "$limit": limit,
            "$where": f"date_time > '{thirty_days_ago}'",
            "$order": "date_time DESC"
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
    required_columns = ['latitude', 'longitude', 'date_of_occurrence']
    missing_required = [col for col in required_columns if col not in data.columns]
    if missing_required:
        print(f"Warning: Missing required crime data columns: {missing_required}")
        return create_mock_crime_data()
    
    # Convert coordinates to numeric values
    data['latitude'] = pd.to_numeric(data['latitude'], errors='coerce')
    data['longitude'] = pd.to_numeric(data['longitude'], errors='coerce')
    
    # Convert and filter date if the column exists
    data['date_of_occurrence'] = pd.to_datetime(data['date_of_occurrence'], errors='coerce')
    cutoff_date = datetime.now() - timedelta(days=30)
    data = data[data['date_of_occurrence'] >= cutoff_date]
    
    # Drop any rows with missing coordinates or dates
    data = data.dropna(subset=['latitude', 'longitude', 'date_of_occurrence'])
    
    if len(data) == 0:
        print("No valid crime data after filtering, using mock data")
        return create_mock_crime_data()
        
    return data 