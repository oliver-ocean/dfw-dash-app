import pandas as pd
import numpy as np
import random
import functools

def fetch_with_fallback(mock_func):
    def decorator(fetch_func):
        @functools.wraps(fetch_func)
        def wrapper(*args, **kwargs):
            try:
                return fetch_func(*args, **kwargs)
            except Exception as e:
                print(f"Error in {fetch_func.__name__}: {e}")
                return mock_func()
        return wrapper
    return decorator

def generate_home_price_data(n=100):
    return pd.DataFrame({
        "Neighborhood": [f"Neighborhood {i}" for i in range(n)],
        "PricePerSqFt": np.random.normal(150, 25, n),
        "MedianHomePrice": np.random.normal(350000, 50000, n),
        "Latitude": np.random.uniform(32.55, 33.05, n),
        "Longitude": np.random.uniform(-97.5, -96.5, n),
        "County": random.choices(["Dallas", "Tarrant", "Denton", "Collin"], k=n)
    })

def generate_leasing_data(n=50):
    return pd.DataFrame({
        "Location": [f"Office {i}" for i in range(n)],
        "AvgLeasePrice": np.random.normal(25, 5, n),
        "Latitude": np.random.uniform(32.55, 33.05, n),
        "Longitude": np.random.uniform(-97.5, -96.5, n),
        "OccupancyRate": np.random.uniform(0.6, 0.95, n)
    })

def generate_traffic_data(n=75):
    return pd.DataFrame({
        "Road": [f"Highway {i}" for i in range(n)],
        "AvgDailyTraffic": np.random.randint(10000, 150000, n),
        "Latitude": np.random.uniform(32.55, 33.05, n),
        "Longitude": np.random.uniform(-97.5, -96.5, n)
    })

def generate_neighborhood_boundaries():
    return {
        "type": "FeatureCollection",
        "features": []
    }