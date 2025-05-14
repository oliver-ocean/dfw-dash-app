import dash_leaflet as dl
import pandas as pd
import random

def load_mock_crime_data(n=100):
    crimes = ["Theft", "Assault", "Burglary", "Vandalism"]
    data = []
    for _ in range(n):
        data.append({
            "Type": random.choice(crimes),
            "Latitude": round(random.uniform(32.6, 33.0), 5),
            "Longitude": round(random.uniform(-97.4, -96.8), 5),
            "Time": f"{random.randint(2023, 2024)}-{random.randint(1,12):02}-01"
        })
    return pd.DataFrame(data)

def render_crime_markers():
    df = load_mock_crime_data()
    markers = [
        dl.Marker(position=[row["Latitude"], row["Longitude"]],
                  children=dl.Tooltip(f"{row['Type']} @ {row['Time']}"))
        for _, row in df.iterrows()
    ]
    return markers