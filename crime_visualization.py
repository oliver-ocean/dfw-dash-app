import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from crime_analysis import CrimeAnalyzer

class CrimeVisualizer:
    """Class to create crime rate visualizations"""
    
    def __init__(self, analyzer: CrimeAnalyzer):
        self.analyzer = analyzer
        
    def calculate_monthly_rates(self, months: int = 12) -> pd.DataFrame:
        """
        Calculate monthly crime rates per 100K population with moving average
        
        Parameters:
        -----------
        months : int
            Number of months of data to analyze
            
        Returns:
        --------
        DataFrame with monthly crime rates and moving averages
        """
        # Get daily stats first
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        
        # Get monthly windows
        stats = self.analyzer.calculate_time_window_stats(
            window_size='1M',
            min_date=start_date,
            max_date=end_date
        )
        
        # Calculate 3-month moving average
        monthly_rates = []
        for city in stats['city'].unique():
            city_stats = stats[stats['city'] == city].copy()
            city_stats = city_stats.sort_values('time_window')
            
            # Calculate moving average of rate_per_100k
            city_stats['moving_avg_rate'] = city_stats['rate_per_100k'].rolling(window=3, min_periods=1).mean()
            
            # Calculate moving average for each crime type
            city_stats['crime_type_rates'] = city_stats['incidents_by_type'].apply(
                lambda x: {
                    crime_type: (count * 100000 / self.analyzer.CITY_POPULATIONS[city])
                    for crime_type, count in x.items()
                }
            )
            
            monthly_rates.append(city_stats)
            
        return pd.concat(monthly_rates, ignore_index=True)
    
    def calculate_spatial_density(self, 
                                latest_month_data: pd.DataFrame,
                                grid_size: float = 0.001,  # roughly 100m
                                smoothing_factor: float = 0.5) -> pd.DataFrame:
        """
        Calculate crime density for map visualization using inverse square distance weighting
        
        Parameters:
        -----------
        latest_month_data : DataFrame
            Crime data for the latest month
        grid_size : float
            Size of grid cells in degrees
        smoothing_factor : float
            Factor to control the smoothing of the density calculation
            
        Returns:
        --------
        DataFrame with grid points and their crime density values
        """
        # Get crime locations
        crime_points = self.analyzer.raw_data[['latitude', 'longitude', 'city']].copy()
        
        # Create grid
        lat_min = crime_points['latitude'].min() - 0.05
        lat_max = crime_points['latitude'].max() + 0.05
        lon_min = crime_points['longitude'].min() - 0.05
        lon_max = crime_points['longitude'].max() + 0.05
        
        lat_range = np.arange(lat_min, lat_max, grid_size)
        lon_range = np.arange(lon_min, lon_max, grid_size)
        
        grid_points = []
        for lat in lat_range:
            for lon in lon_range:
                # Calculate density for this point
                distances = np.sqrt(
                    (crime_points['latitude'] - lat)**2 + 
                    (crime_points['longitude'] - lon)**2
                )
                
                # Inverse square distance weighting
                weights = 1 / (distances + smoothing_factor)**2
                density = weights.sum()
                
                # Get city based on nearest crime point
                nearest_idx = distances.argmin()
                city = crime_points.iloc[nearest_idx]['city']
                
                grid_points.append({
                    'latitude': lat,
                    'longitude': lon,
                    'density': density,
                    'city': city
                })
        
        grid_df = pd.DataFrame(grid_points)
        
        # Normalize density values to 0-1 range for each city
        for city in grid_df['city'].unique():
            city_mask = grid_df['city'] == city
            city_densities = grid_df.loc[city_mask, 'density']
            grid_df.loc[city_mask, 'density_normalized'] = (
                (city_densities - city_densities.min()) / 
                (city_densities.max() - city_densities.min())
            )
        
        return grid_df
    
    def get_color_opacity(self, density: float) -> Tuple[str, float]:
        """
        Get color and opacity for a given density value
        
        Parameters:
        -----------
        density : float
            Normalized density value (0-1)
            
        Returns:
        --------
        tuple of (color_hex, opacity)
        """
        # Use a red color with varying opacity
        opacity = 0.1 + (density * 0.6)  # opacity ranges from 0.1 to 0.7
        return '#FF0000', opacity
    
    def generate_map_data(self) -> Dict:
        """
        Generate all necessary data for map visualization
        
        Returns:
        --------
        Dictionary containing:
        - monthly_rates: DataFrame of monthly crime rates
        - spatial_density: DataFrame of spatial density values
        - latest_month: Latest month's statistics
        """
        # Get monthly rates
        monthly_rates = self.calculate_monthly_rates()
        
        # Get latest month's data
        latest_month = monthly_rates[
            monthly_rates['time_window'] == monthly_rates['time_window'].max()
        ]
        
        # Calculate spatial density
        spatial_density = self.calculate_spatial_density(latest_month)
        
        return {
            'monthly_rates': monthly_rates,
            'spatial_density': spatial_density,
            'latest_month': latest_month
        }

def test_visualization():
    """Test the crime visualization functionality"""
    from live_crime_data import fetch_crime_data
    
    # Fetch crime data
    print("Fetching crime data...")
    data = fetch_crime_data()
    
    # Create analyzer and visualizer
    analyzer = CrimeAnalyzer(data)
    visualizer = CrimeVisualizer(analyzer)
    
    # Test monthly rates
    print("\nCalculating monthly crime rates...")
    monthly_rates = visualizer.calculate_monthly_rates()
    print("\nSample of monthly rates:")
    print(monthly_rates[['time_window', 'city', 'rate_per_100k', 'moving_avg_rate']].head(2).to_string())
    
    # Test spatial density
    print("\nCalculating spatial density...")
    latest_month = monthly_rates[monthly_rates['time_window'] == monthly_rates['time_window'].max()]
    density = visualizer.calculate_spatial_density(latest_month)
    print("\nSample of density values:")
    print(density.head(2).to_string())
    
    # Print sample color/opacity values
    print("\nSample color/opacity values:")
    for d in [0.0, 0.25, 0.5, 0.75, 1.0]:
        color, opacity = visualizer.get_color_opacity(d)
        print(f"Density {d:.2f}: Color = {color}, Opacity = {opacity:.2f}")

if __name__ == "__main__":
    test_visualization() 