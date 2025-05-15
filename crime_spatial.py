import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from typing import List, Tuple, Dict
from datetime import datetime, timedelta

class CrimeSpatialAnalyzer:
    """
    Advanced spatial analysis for crime data using anchor points and inverse square distance weighting.
    This class creates a mesh of anchor points and computes crime risk scores for any coordinate
    using weighted averages based on inverse square distance to anchor points.
    """
    
    def __init__(self, data: pd.DataFrame, grid_size: int = 100):
        """
        Initialize the spatial analyzer
        
        Parameters:
        -----------
        data : DataFrame
            Crime data with columns: latitude, longitude, date_of_occurrence, nibrs_crime_category
        grid_size : int
            Number of anchor points to create in each dimension
        """
        self.raw_data = data.copy()
        self.raw_data['date_of_occurrence'] = pd.to_datetime(self.raw_data['date_of_occurrence'])
        self.grid_size = grid_size
        self.anchor_points = None
        self.anchor_scores = None
        
        # Initialize anchor points and their scores
        self._initialize_anchor_points()
        
    def _initialize_anchor_points(self):
        """Create a mesh of anchor points and calculate their base scores"""
        # Get data boundaries with buffer
        lat_min = self.raw_data['latitude'].min() - 0.05
        lat_max = self.raw_data['latitude'].max() + 0.05
        lon_min = self.raw_data['longitude'].min() - 0.05
        lon_max = self.raw_data['longitude'].max() + 0.05
        
        # Create anchor point grid
        lat_range = np.linspace(lat_min, lat_max, self.grid_size)
        lon_range = np.linspace(lon_min, lon_max, self.grid_size)
        lat_grid, lon_grid = np.meshgrid(lat_range, lon_range)
        self.anchor_points = np.column_stack((lat_grid.ravel(), lon_grid.ravel()))
        
        # Calculate base scores for anchor points
        self._update_anchor_scores()
        
    def _update_anchor_scores(self, time_decay: bool = True):
        """
        Update scores for all anchor points
        
        Parameters:
        -----------
        time_decay : bool
            Whether to apply time-based decay to crime weights
        """
        # Get crime locations
        crime_points = self.raw_data[['latitude', 'longitude']].values
        
        if time_decay:
            # Calculate time weights
            days_ago = (datetime.now() - self.raw_data['date_of_occurrence']).dt.days
            time_weights = np.exp(-days_ago / 365)  # Exponential decay over a year
        else:
            time_weights = np.ones(len(self.raw_data))
            
        # Calculate distances between anchor points and crime locations
        distances = cdist(self.anchor_points, crime_points)
        
        # Calculate weights using inverse square distance
        weights = 1 / (distances ** 2 + 1e-10)  # Add small constant to avoid division by zero
        
        # Apply time weights to the distance weights
        weighted_crimes = weights * time_weights
        
        # Sum weights for each anchor point
        self.anchor_scores = weighted_crimes.sum(axis=1)
        
        # Normalize scores to 0-1 range
        self.anchor_scores = (self.anchor_scores - self.anchor_scores.min()) / \
                           (self.anchor_scores.max() - self.anchor_scores.min())
    
    def get_score(self, lat: float, lon: float) -> float:
        """
        Calculate crime risk score for a specific coordinate
        
        Parameters:
        -----------
        lat : float
            Latitude of the point
        lon : float
            Longitude of the point
            
        Returns:
        --------
        float : Risk score between 0 and 1
        """
        # Calculate distances to all anchor points
        point = np.array([[lat, lon]])
        distances = cdist(point, self.anchor_points)[0]
        
        # Calculate weights using inverse square distance
        weights = 1 / (distances ** 2 + 1e-10)
        weights = weights / weights.sum()  # Normalize weights
        
        # Calculate weighted average of anchor point scores
        score = np.sum(weights * self.anchor_scores)
        
        return score
    
    def get_scores_batch(self, points: np.ndarray) -> np.ndarray:
        """
        Calculate crime risk scores for multiple coordinates at once
        
        Parameters:
        -----------
        points : np.ndarray
            Array of shape (n, 2) containing latitude and longitude pairs
            
        Returns:
        --------
        np.ndarray : Array of risk scores between 0 and 1
        """
        # Calculate distances to all anchor points
        distances = cdist(points, self.anchor_points)
        
        # Calculate weights using inverse square distance
        weights = 1 / (distances ** 2 + 1e-10)
        weights = weights / weights.sum(axis=1, keepdims=True)  # Normalize weights
        
        # Calculate weighted average of anchor point scores
        scores = np.sum(weights * self.anchor_scores, axis=1)
        
        return scores
    
    def get_high_risk_areas(self, threshold: float = 0.75) -> pd.DataFrame:
        """
        Get locations of high-risk areas
        
        Parameters:
        -----------
        threshold : float
            Score threshold for high-risk classification (0-1)
            
        Returns:
        --------
        DataFrame with high-risk anchor points and their scores
        """
        high_risk_mask = self.anchor_scores >= threshold
        high_risk_points = self.anchor_points[high_risk_mask]
        high_risk_scores = self.anchor_scores[high_risk_mask]
        
        return pd.DataFrame({
            'latitude': high_risk_points[:, 0],
            'longitude': high_risk_points[:, 1],
            'risk_score': high_risk_scores
        })
    
    def analyze_location_risk(self, lat: float, lon: float, radius: float = 0.02) -> Dict:
        """
        Detailed risk analysis for a specific location
        
        Parameters:
        -----------
        lat : float
            Latitude of the point
        lon : float
            Longitude of the point
        radius : float
            Radius in degrees to analyze (0.02 ≈ 2km)
            
        Returns:
        --------
        Dictionary containing:
        - current_risk: current risk score
        - nearby_crimes: recent crimes within radius
        - trend: risk score trend over last 3 months
        """
        # Calculate current risk score
        current_risk = self.get_score(lat, lon)
        
        # Get nearby crimes
        distances = np.sqrt(
            (self.raw_data['latitude'] - lat)**2 + 
            (self.raw_data['longitude'] - lon)**2
        )
        nearby = self.raw_data[distances <= radius].copy()
        
        # Calculate 3-month trend
        three_months_ago = datetime.now() - timedelta(days=90)
        recent_nearby = nearby[nearby['date_of_occurrence'] >= three_months_ago]
        monthly_counts = recent_nearby.groupby(
            recent_nearby['date_of_occurrence'].dt.to_period('M')
        ).size()
        
        return {
            'current_risk': current_risk,
            'nearby_crimes_count': len(nearby),
            'recent_crimes_count': len(recent_nearby),
            'monthly_trend': monthly_counts.to_dict(),
            'crime_types': nearby['nibrs_crime_category'].value_counts().to_dict()
        }

def test_spatial_analyzer():
    """Test the spatial analysis functionality"""
    from live_crime_data import fetch_crime_data
    
    # Fetch crime data
    print("Fetching crime data...")
    data = fetch_crime_data()
    
    # Create analyzer
    analyzer = CrimeSpatialAnalyzer(data)
    
    # Test single point scoring
    test_lat, test_lon = 32.78, -96.8  # Downtown Dallas
    score = analyzer.get_score(test_lat, test_lon)
    print(f"\nRisk score for downtown Dallas: {score:.3f}")
    
    # Test batch scoring
    test_points = np.array([
        [32.78, -96.8],  # Downtown Dallas
        [32.75, -97.33],  # Downtown Fort Worth
        [32.85, -96.75]  # North Dallas
    ])
    scores = analyzer.get_scores_batch(test_points)
    print("\nBatch scoring results:")
    for point, score in zip(test_points, scores):
        print(f"Location ({point[0]:.2f}, {point[1]:.2f}): {score:.3f}")
    
    # Test high-risk areas
    high_risk = analyzer.get_high_risk_areas(threshold=0.75)
    print(f"\nFound {len(high_risk)} high-risk areas")
    print("\nSample high-risk locations:")
    print(high_risk.head().to_string())
    
    # Test detailed location analysis
    analysis = analyzer.analyze_location_risk(test_lat, test_lon)
    print("\nDetailed analysis for downtown Dallas:")
    print(f"Current risk score: {analysis['current_risk']:.3f}")
    print(f"Nearby crimes (last year): {analysis['nearby_crimes_count']}")
    print(f"Recent crimes (last 3 months): {analysis['recent_crimes_count']}")
    print("\nCrime type breakdown:")
    for crime_type, count in analysis['crime_types'].items():
        print(f"  {crime_type}: {count}")

if __name__ == "__main__":
    test_spatial_analyzer() 