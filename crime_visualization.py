import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from crime_analysis import CrimeAnalyzer
from crime_stats_db import CrimeStatsDB

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

class CrimeVisualization:
    """Class to handle crime data visualization using pre-computed statistics"""
    
    def __init__(self, grid_size: int = 100):
        """Initialize with a CrimeStatsDB instance"""
        self.db = CrimeStatsDB(grid_size=grid_size)
        
    def get_heatmap_data(self) -> pd.DataFrame:
        """Get current heatmap data from the database"""
        return self.db.get_current_heatmap_data()
    
    def get_location_stats(self, lat: float, lon: float, radius: float = 0.02) -> dict:
        """Get crime statistics for a specific location"""
        return self.db.get_location_stats(lat, lon, radius)
    
    def update_database(self, force: bool = False):
        """
        Update the crime statistics database.
        This should be called periodically (e.g., daily) to keep the data current.
        
        Parameters:
        -----------
        force : bool
            If True, force update even if data is current
        """
        try:
            from live_crime_data import fetch_crime_data
            
            # Check if we need to update
            current_data = self.db.get_current_heatmap_data()
            if not force and not current_data.empty:
                latest_month = self.db.stats_df['month'].max()
                if latest_month and latest_month.month == datetime.now().month:
                    print("Database is current, no update needed")
                    return
            
            # Fetch new data and update
            print("Fetching new crime data for database update...")
            crime_data = fetch_crime_data(limit=1000)  # Get more data for better statistics
            if not crime_data.empty:
                print("Updating crime statistics database...")
                self.db.update_stats(crime_data)
                print("Database update complete")
            else:
                print("No new data available for update")
                
        except Exception as e:
            print(f"Error updating crime database: {str(e)}")
            print("Continuing with existing data")
    
    def get_trend_analysis(self, lat: float, lon: float) -> dict:
        """
        Get detailed trend analysis for a location
        
        Parameters:
        -----------
        lat : float
            Latitude of the point
        lon : float
            Longitude of the point
            
        Returns:
        --------
        Dictionary containing:
        - monthly_trend: List of monthly statistics
        - current_risk: Current risk score
        - recent_stats: Dictionary of recent crime statistics
        """
        stats = self.get_location_stats(lat, lon)
        if not stats:
            return None
            
        return {
            'trend': stats['monthly_trend'],
            'current_risk': stats['current_risk'],
            'recent_stats': stats['recent_stats']
        }

def create_crime_markers(resolution: int = 50):
    """Create crime visualization markers using pre-computed statistics"""
    viz = CrimeVisualization(grid_size=resolution)
    
    # Try to update the database if needed
    viz.update_database()
    
    # Get current heatmap data
    heatmap_data = viz.get_heatmap_data()
    
    if heatmap_data is None or heatmap_data.empty:
        print("No crime data available for visualization")
        return []
    
    return heatmap_data.to_dict('records')

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