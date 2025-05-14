import pandas as pd
import requests
from io import StringIO

def fetch_traffic_data():
    url = "https://gis-txdot.opendata.arcgis.com/datasets/d5f56ecd2b274b4d8dc3c2d6fe067d37_0.csv"
    response = requests.get(url)
    if response.status_code == 200:
        df = pd.read_csv(StringIO(response.text))
        df = df[df['County'] == 'Dallas']
        return df
    else:
        return pd.DataFrame()