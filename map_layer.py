import pandas as pd
import numpy as np
from typing import Dict, List
from crime_stats_db import CrimeStatsDB
from datetime import datetime, timedelta

class CrimeMapLayer:
    """Class to create crime density map layer using pre-computed statistics"""
    
    def __init__(self, grid_size: int = 100):
        """Initialize the map layer"""
        self.stats_db = CrimeStatsDB(grid_size=grid_size)
        self.update_data()
    
    def update_data(self):
        """Update crime statistics database with fresh data"""
        from live_crime_data import fetch_crime_data
        
        # Fetch latest data
        data = fetch_crime_data()
        
        # Update statistics database
        self.stats_db.update_stats(data)
    
    def get_density_overlay(self) -> List[Dict]:
        """
        Get density overlay data for map visualization
        
        Returns:
        --------
        List of dictionaries containing:
        - lat: latitude
        - lon: longitude
        - color: hex color code
        - opacity: opacity value (0-1)
        - weight: point weight
        - risk_score: crime risk score
        """
        # Get current heatmap data
        heatmap_data = self.stats_db.get_current_heatmap_data()
        
        overlay_points = []
        for _, point in heatmap_data.iterrows():
            # Use risk score to determine color and opacity
            color = '#FF0000'  # Red base color
            opacity = 0.1 + (point['risk_score'] * 0.6)  # Scale opacity from 0.1 to 0.7
            
            overlay_points.append({
                'lat': point['latitude'],
                'lon': point['longitude'],
                'color': color,
                'opacity': opacity,
                'weight': 2,
                'risk_score': point['risk_score']
            })
        
        return overlay_points
    
    def get_location_analysis(self, lat: float, lon: float, radius_km: float = 2.0) -> Dict:
        """
        Get detailed analysis for a specific location
        
        Parameters:
        -----------
        lat : float
            Latitude of the point
        lon : float
            Longitude of the point
        radius_km : float
            Radius in kilometers to analyze
            
        Returns:
        --------
        Dictionary containing detailed risk analysis
        """
        # Convert radius from km to degrees (approximately)
        radius_deg = radius_km / 111.0
        
        # Get location statistics from database
        return self.stats_db.get_location_stats(lat, lon, radius=radius_deg)
    
    def get_high_risk_markers(self, threshold: float = 0.75) -> List[Dict]:
        """
        Get markers for high-risk areas
        
        Parameters:
        -----------
        threshold : float
            Risk score threshold for high-risk classification
            
        Returns:
        --------
        List of dictionaries containing marker data for high-risk areas
        """
        # Get current heatmap data
        heatmap_data = self.stats_db.get_current_heatmap_data()
        high_risk = heatmap_data[heatmap_data['risk_score'] >= threshold]
        
        markers = []
        for _, point in high_risk.iterrows():
            markers.append({
                'lat': point['latitude'],
                'lon': point['longitude'],
                'color': '#FF0000',
                'opacity': 0.9,
                'weight': 3,
                'risk_score': point['risk_score']
            })
        
        return markers

def test_map_layer():
    """Test the map layer functionality"""
    layer = CrimeMapLayer(grid_size=50)  # Using smaller grid for testing
    
    # Test density overlay
    print("Testing density overlay...")
    overlay = layer.get_density_overlay()
    print(f"\nGenerated {len(overlay)} overlay points")
    print("\nSample overlay point:")
    print(overlay[0])
    
    # Test high-risk markers
    print("\nTesting high-risk markers...")
    markers = layer.get_high_risk_markers()
    print(f"\nFound {len(markers)} high-risk areas")
    if markers:
        print("\nSample high-risk marker:")
        print(markers[0])
    
    # Test location analysis
    print("\nTesting location analysis...")
    test_lat, test_lon = 32.78, -96.8  # Downtown Dallas
    analysis = layer.get_location_analysis(test_lat, test_lon)
    if analysis:
        print("\nLocation analysis results:")
        print(f"Risk score: {analysis['current_risk']:.3f}")
        print("\nRecent statistics (3-month average):")
        for category, count in analysis['recent_stats'].items():
            print(f"  {category}: {count:.2f}")
        print("\nMonthly trend (last 3 months):")
        monthly_trend = analysis['monthly_trend'][-3:]
        for month in monthly_trend:
            print(f"  {month['month'].strftime('%Y-%m')}: {month['risk_score']:.3f}")

if __name__ == "__main__":
    test_map_layer() 