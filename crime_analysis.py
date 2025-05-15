import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

class CrimeAnalyzer:
    """Class to analyze crime data over time and space"""
    
    # Population estimates for rate calculations (2023 estimates)
    CITY_POPULATIONS = {
        'Dallas': 1_304_000,
        'Fort Worth': 958_692
    }
    
    # Area in square miles
    CITY_AREAS = {
        'Dallas': 383.0,
        'Fort Worth': 355.6
    }
    
    def __init__(self, data: pd.DataFrame):
        """Initialize with crime data DataFrame"""
        self.raw_data = data.copy()
        self.raw_data['date_of_occurrence'] = pd.to_datetime(self.raw_data['date_of_occurrence'])
        
    def calculate_time_window_stats(self, 
                                  window_size: str = '1D',
                                  min_date: datetime = None,
                                  max_date: datetime = None) -> pd.DataFrame:
        """
        Calculate crime statistics for specified time windows
        
        Parameters:
        -----------
        window_size : str
            Time window size ('1D' for daily, '7D' for weekly, '1M' for monthly)
        min_date : datetime
            Start date for analysis (defaults to earliest date in data)
        max_date : datetime
            End date for analysis (defaults to latest date in data)
            
        Returns:
        --------
        DataFrame with columns:
            - time_window: start of time window
            - total_incidents: total number of crimes
            - incidents_by_type: dict of crime types and counts
            - rate_per_100k: crimes per 100,000 population
            - rate_per_sqmile: crimes per square mile
            - city: city name
        """
        data = self.raw_data.copy()
        
        # Filter date range if specified
        if min_date:
            data = data[data['date_of_occurrence'] >= min_date]
        if max_date:
            data = data[data['date_of_occurrence'] <= max_date]
            
        # Group by time window and city
        grouped = data.groupby([
            pd.Grouper(key='date_of_occurrence', freq=window_size),
            'city'
        ])
        
        # Calculate statistics
        stats = []
        for (window, city), group in grouped:
            # Count incidents by type
            type_counts = group['nibrs_crime_category'].value_counts().to_dict()
            
            # Calculate rates
            population = self.CITY_POPULATIONS.get(city, 0)
            area = self.CITY_AREAS.get(city, 0)
            total_incidents = len(group)
            
            stats.append({
                'time_window': window,
                'city': city,
                'total_incidents': total_incidents,
                'incidents_by_type': type_counts,
                'rate_per_100k': (total_incidents * 100000 / population) if population > 0 else 0,
                'rate_per_sqmile': total_incidents / area if area > 0 else 0
            })
        
        return pd.DataFrame(stats)
    
    def calculate_moving_average(self,
                               window_days: int = 7,
                               by_type: bool = False) -> pd.DataFrame:
        """
        Calculate moving average of crime rates
        
        Parameters:
        -----------
        window_days : int
            Number of days for moving average window
        by_type : bool
            Whether to calculate separate averages for each crime type
            
        Returns:
        --------
        DataFrame with moving averages by city (and crime type if by_type=True)
        """
        data = self.raw_data.copy()
        
        # Create daily counts
        if by_type:
            # Group by date, city, and crime type
            daily = data.groupby([
                data['date_of_occurrence'].dt.date,
                'city',
                'nibrs_crime_category'
            ]).size().reset_index(name='count')
            
            # Calculate moving average for each city and crime type
            averages = []
            for city in daily['city'].unique():
                city_data = daily[daily['city'] == city]
                for crime_type in city_data['nibrs_crime_category'].unique():
                    type_data = city_data[city_data['nibrs_crime_category'] == crime_type]
                    ma = type_data.set_index('date_of_occurrence')['count'].rolling(window=window_days).mean()
                    averages.append(pd.DataFrame({
                        'date': ma.index,
                        'city': city,
                        'crime_type': crime_type,
                        'moving_average': ma.values
                    }))
            
            return pd.concat(averages, ignore_index=True)
        else:
            # Group by date and city only
            daily = data.groupby([
                data['date_of_occurrence'].dt.date,
                'city'
            ]).size().reset_index(name='count')
            
            # Calculate moving average for each city
            averages = []
            for city in daily['city'].unique():
                city_data = daily[daily['city'] == city]
                ma = city_data.set_index('date_of_occurrence')['count'].rolling(window=window_days).mean()
                averages.append(pd.DataFrame({
                    'date': ma.index,
                    'city': city,
                    'moving_average': ma.values
                }))
            
            return pd.concat(averages, ignore_index=True)
    
    def get_hotspots(self,
                     grid_size: float = 0.01,  # degrees (roughly 1km)
                     min_date: datetime = None,
                     max_date: datetime = None) -> pd.DataFrame:
        """
        Calculate crime hotspots based on incident density
        
        Parameters:
        -----------
        grid_size : float
            Size of grid cells in degrees
        min_date : datetime
            Start date for analysis
        max_date : datetime
            End date for analysis
            
        Returns:
        --------
        DataFrame with columns:
            - center_lat: center latitude of grid cell
            - center_lon: center longitude of grid cell
            - incident_count: number of incidents in cell
            - crime_types: dict of crime types and counts
            - city: city name
        """
        data = self.raw_data.copy()
        
        # Filter date range if specified
        if min_date:
            data = data[data['date_of_occurrence'] >= min_date]
        if max_date:
            data = data[data['date_of_occurrence'] <= max_date]
        
        # Create grid cells
        data['grid_lat'] = (data['latitude'] / grid_size).astype(int) * grid_size
        data['grid_lon'] = (data['longitude'] / grid_size).astype(int) * grid_size
        
        # Group by grid cell and city
        grouped = data.groupby(['grid_lat', 'grid_lon', 'city'])
        
        hotspots = []
        for (lat, lon, city), group in grouped:
            # Count incidents by type
            type_counts = group['nibrs_crime_category'].value_counts().to_dict()
            
            hotspots.append({
                'center_lat': lat + grid_size/2,
                'center_lon': lon + grid_size/2,
                'incident_count': len(group),
                'crime_types': type_counts,
                'city': city
            })
        
        return pd.DataFrame(hotspots)

def test_analysis():
    """Test the crime analysis functionality"""
    from live_crime_data import fetch_crime_data
    
    # Fetch crime data
    print("Fetching crime data...")
    data = fetch_crime_data()
    
    # Create analyzer
    analyzer = CrimeAnalyzer(data)
    
    # Test daily statistics
    print("\nCalculating daily statistics...")
    daily_stats = analyzer.calculate_time_window_stats('1D')
    print("\nSample of daily statistics:")
    print(daily_stats.head(2).to_string())
    
    # Test weekly moving average
    print("\nCalculating 7-day moving average...")
    ma = analyzer.calculate_moving_average(7)
    print("\nSample of moving averages:")
    print(ma.head(2).to_string())
    
    # Test hotspots
    print("\nCalculating crime hotspots...")
    hotspots = analyzer.get_hotspots()
    print("\nSample of hotspots:")
    print(hotspots.head(2).to_string())

if __name__ == "__main__":
    test_analysis() 