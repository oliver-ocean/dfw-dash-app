import pandas as pd
import requests

def fetch_crime_data(limit=100):
    url = "https://www.dallasopendata.com/resource/qv6i-rri7.json"
    params = {
        "$limit": limit,
        "$order": "date_of_occurrence DESC"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = pd.DataFrame(response.json())
        data['latitude'] = pd.to_numeric(data['latitude'], errors='coerce')
        data['longitude'] = pd.to_numeric(data['longitude'], errors='coerce')
        return data.dropna(subset=['latitude', 'longitude'])
    else:
        return pd.DataFrame()