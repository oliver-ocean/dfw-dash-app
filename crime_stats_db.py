import pandas as pd
import numpy as np
from scipy.spatial.distance import cdist
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import os

class CrimeStatsDB:
    """
    Manages a database of pre-computed crime statistics for efficient real-time rendering.
    Stores monthly scores for each anchor point in a mesh grid.
    """
    
    def __init__(self, grid_size: int = 100):
        """
        Initialize the crime statistics database
        
        Parameters:
        -----------
        grid_size : int
            Number of anchor points in each dimension
        """
        self.grid_size = grid_size
        self.db_path = 'data/crime_stats.csv'
        self.anchor_points = None
        self.stats_df = None
        
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Initialize or load the database
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize or load the crime statistics database"""
        if os.path.exists(self.db_path):
            self.stats_df = pd.read_csv(self.db_path)
            # Convert month column back to datetime
            self.stats_df['month'] = pd.to_datetime(self.stats_df['month'])
            # Reconstruct anchor points from unique lat/lon in database
            unique_points = self.stats_df[['latitude', 'longitude']].drop_duplicates()
            self.anchor_points = unique_points.values
        else:
            self._create_empty_db()
    
    def _create_empty_db(self):
        """Create an empty database with anchor points"""
        # Define DFW area boundaries
        lat_min, lat_max = 32.64, 33.04
        lon_min, lon_max = -96.95, -96.49
        
        # Create anchor point grid
        lat_range = np.linspace(lat_min, lat_max, self.grid_size)
        lon_range = np.linspace(lon_min, lon_max, self.grid_size)
        lat_grid, lon_grid = np.meshgrid(lat_range, lon_range)
        self.anchor_points = np.column_stack((lat_grid.ravel(), lon_grid.ravel()))
        
        # Create empty DataFrame with anchor points
        points_df = pd.DataFrame(
            self.anchor_points,
            columns=['latitude', 'longitude']
        )
        
        # Create exactly 12 months of data points
        end_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)  # First day of current month
        start_date = (end_date - timedelta(days=365)).replace(day=1)  # First day of start month
        months = pd.date_range(start_date, end_date, freq='MS')
        
        # Validate we have exactly 12 months
        if len(months) > 12:
            months = months[-12:]  # Take the most recent 12 months
        elif len(months) < 12:
            # Adjust start_date to ensure 12 months
            start_date = (end_date - timedelta(days=365)).replace(day=1)
            months = pd.date_range(start_date, end_date, freq='MS')
        
        # Create empty stats DataFrame
        stats_data = []
        for _, point in points_df.iterrows():
            for month in months:
                stats_data.append({
                    'latitude': point['latitude'],
                    'longitude': point['longitude'],
                    'month': month,
                    'risk_score': 0.0,
                    'crime_count': 0.0,
                    'violent_count': 0.0,
                    'property_count': 0.0,
                    'other_count': 0.0
                })
        
        self.stats_df = pd.DataFrame(stats_data)
        
        # Validate the data
        month_count = len(self.stats_df['month'].unique())
        assert month_count == 12, f"Expected 12 months of data, but got {month_count} months"
        
        self.stats_df.to_csv(self.db_path, index=False)
    
    def update_stats(self, crime_data: pd.DataFrame):
        """
        Update crime statistics using new crime data
        
        Parameters:
        -----------
        crime_data : DataFrame
            Crime data with columns: latitude, longitude, date_of_occurrence, nibrs_crime_category
        """
        # Ensure date column is datetime
        crime_data['date_of_occurrence'] = pd.to_datetime(crime_data['date_of_occurrence'])
        
        # Create monthly bins
        crime_data['month'] = crime_data['date_of_occurrence'].dt.to_period('M').astype(str)
        crime_data['month'] = pd.to_datetime(crime_data['month'])
        
        # Keep only the last 12 months of data
        latest_month = crime_data['month'].max()
        twelve_months_ago = (latest_month - pd.DateOffset(months=11)).replace(day=1)
        crime_data = crime_data[crime_data['month'] >= twelve_months_ago]
        
        # Categorize crimes
        crime_data['category'] = crime_data['nibrs_crime_category'].map(
            lambda x: 'violent' if x in ['ASSAULT', 'HOMICIDE', 'ROBBERY'] 
            else ('property' if x in ['THEFT', 'BURGLARY', 'AUTO THEFT'] 
            else 'other')
        )
        
        # Reset database for the time period we're updating
        self.stats_df = self.stats_df[
            (self.stats_df['month'] < twelve_months_ago) |
            (self.stats_df['month'] > latest_month)
        ]
        
        # Ensure we have entries for all anchor points for each month
        months = pd.date_range(twelve_months_ago, latest_month, freq='MS')
        new_records = []
        for _, point in pd.DataFrame(self.anchor_points, columns=['latitude', 'longitude']).iterrows():
            for month in months:
                new_records.append({
                    'latitude': point['latitude'],
                    'longitude': point['longitude'],
                    'month': month,
                    'risk_score': 0.0,
                    'crime_count': 0.0,
                    'violent_count': 0.0,
                    'property_count': 0.0,
                    'other_count': 0.0
                })
        
        self.stats_df = pd.concat([self.stats_df, pd.DataFrame(new_records)], ignore_index=True)
        
        # Process each month
        unique_months = crime_data['month'].unique()
        for month in unique_months:
            month_crimes = crime_data[crime_data['month'] == month]
            
            # Calculate distances between anchor points and crimes
            crime_locations = month_crimes[['latitude', 'longitude']].values
            distances = cdist(self.anchor_points, crime_locations)
            
            # Calculate weights using inverse square distance
            weights = 1 / (distances ** 2 + 1e-10)
            
            # Calculate crime counts and scores for each anchor point
            for i, anchor_point in enumerate(self.anchor_points):
                point_weights = weights[i]
                
                # Update stats for this point and month
                mask = (
                    (self.stats_df['latitude'] == anchor_point[0]) &
                    (self.stats_df['longitude'] == anchor_point[1]) &
                    (self.stats_df['month'] == month)
                )
                
                # Calculate weighted counts
                total_weight = float(point_weights.sum())
                violent_weight = float(point_weights[month_crimes['category'] == 'violent'].sum())
                property_weight = float(point_weights[month_crimes['category'] == 'property'].sum())
                other_weight = float(point_weights[month_crimes['category'] == 'other'].sum())
                
                self.stats_df.loc[mask, 'crime_count'] = total_weight
                self.stats_df.loc[mask, 'violent_count'] = violent_weight
                self.stats_df.loc[mask, 'property_count'] = property_weight
                self.stats_df.loc[mask, 'other_count'] = other_weight
        
        # Normalize scores for each month
        for month in unique_months:
            month_mask = self.stats_df['month'] == month
            month_counts = self.stats_df.loc[month_mask, 'crime_count']
            if month_counts.max() > month_counts.min():  # Only normalize if there's variation
                self.stats_df.loc[month_mask, 'risk_score'] = (
                    (month_counts - month_counts.min()) /
                    (month_counts.max() - month_counts.min())
                )
        
        # Validate we maintain 12 months of data
        month_count = len(self.stats_df['month'].unique())
        assert month_count <= 12, f"Database contains {month_count} months of data, expected <= 12"
        
        # Save updated database
        self.stats_df.to_csv(self.db_path, index=False)
    
    def get_location_stats(self, lat: float, lon: float, radius: float = 0.02) -> Dict:
        """
        Get crime statistics for a specific location
        
        Parameters:
        -----------
        lat : float
            Latitude of the point
        lon : float
            Longitude of the point
        radius : float
            Radius in degrees to analyze
            
        Returns:
        --------
        Dictionary containing location statistics
        """
        # Find nearby anchor points
        distances = np.sqrt(
            (self.anchor_points[:, 0] - lat)**2 +
            (self.anchor_points[:, 1] - lon)**2
        )
        nearby_indices = distances <= radius
        
        if not any(nearby_indices):
            return None
        
        # Calculate weights for nearby points
        weights = 1 / (distances[nearby_indices] ** 2 + 1e-10)
        weights = weights / weights.sum()
        
        # Get stats for nearby points
        nearby_points = self.anchor_points[nearby_indices]
        stats = []
        
        for point, weight in zip(nearby_points, weights):
            point_stats = self.stats_df[
                (self.stats_df['latitude'] == point[0]) &
                (self.stats_df['longitude'] == point[1])
            ].copy()
            point_stats['weight'] = weight
            stats.append(point_stats)
        
        if not stats:
            return None
            
        stats_df = pd.concat(stats)
        
        # Calculate weighted averages by month
        monthly_stats = []
        for month in stats_df['month'].unique():
            month_data = stats_df[stats_df['month'] == month]
            month_weights = month_data['weight'].values
            
            monthly_stats.append({
                'month': month,
                'risk_score': np.average(month_data['risk_score'], weights=month_weights),
                'crime_count': np.average(month_data['crime_count'], weights=month_weights),
                'violent_count': np.average(month_data['violent_count'], weights=month_weights),
                'property_count': np.average(month_data['property_count'], weights=month_weights),
                'other_count': np.average(month_data['other_count'], weights=month_weights)
            })
        
        monthly_stats_df = pd.DataFrame(monthly_stats).sort_values('month')
        
        return {
            'monthly_trend': monthly_stats_df.to_dict('records'),
            'current_risk': monthly_stats_df.iloc[-1]['risk_score'],
            'recent_stats': {
                'total': monthly_stats_df.iloc[-3:]['crime_count'].mean(),
                'violent': monthly_stats_df.iloc[-3:]['violent_count'].mean(),
                'property': monthly_stats_df.iloc[-3:]['property_count'].mean(),
                'other': monthly_stats_df.iloc[-3:]['other_count'].mean()
            }
        }
    
    def get_current_heatmap_data(self) -> pd.DataFrame:
        """
        Get the latest month's data for heatmap visualization
        
        Returns:
        --------
        DataFrame with latest risk scores for all anchor points
        """
        latest_month = self.stats_df['month'].max()
        return self.stats_df[
            self.stats_df['month'] == latest_month
        ][['latitude', 'longitude', 'risk_score']]

def test_crime_stats_db():
    """Test the crime statistics database functionality"""
    from live_crime_data import fetch_crime_data
    
    # Create database
    print("Initializing crime stats database...")
    db = CrimeStatsDB(grid_size=50)  # Using smaller grid for testing
    
    # Fetch some crime data
    print("\nFetching crime data...")
    crime_data = fetch_crime_data()
    
    # Update database
    print("\nUpdating crime statistics...")
    db.update_stats(crime_data)
    
    # Test location query
    test_lat, test_lon = 32.78, -96.8  # Downtown Dallas
    print(f"\nQuerying statistics for downtown Dallas ({test_lat}, {test_lon})...")
    stats = db.get_location_stats(test_lat, test_lon)
    
    if stats:
        print(f"\nCurrent risk score: {stats['current_risk']:.3f}")
        print("\nRecent statistics (3-month average):")
        for category, count in stats['recent_stats'].items():
            print(f"  {category}: {count:.2f}")
        
        print("\nMonthly trend (last 3 months):")
        monthly_trend = stats['monthly_trend'][-3:]
        for month in monthly_trend:
            print(f"  {month['month'].strftime('%Y-%m')}: {month['risk_score']:.3f}")
    
    # Test heatmap data
    print("\nGetting heatmap data...")
    heatmap_data = db.get_current_heatmap_data()
    print(f"\nHeatmap points: {len(heatmap_data)}")
    print("\nSample heatmap data:")
    print(heatmap_data.head().to_string())

if __name__ == "__main__":
    test_crime_stats_db() 