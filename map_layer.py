import pandas as pd
import numpy as np
from typing import Dict, List
from crime_stats_db import CrimeStatsDB
from datetime import datetime, timedelta
from crime_visualization import CrimeVisualization

class CrimeMapLayer:
    """Handles the crime data layer for the map"""
    
    def __init__(self, resolution: int = 100):
        """Initialize with visualization system"""
        self.viz = CrimeVisualization(grid_size=resolution)
        
    def get_heatmap_data(self):
        """Get current heatmap data for visualization"""
        return self.viz.get_heatmap_data()
    
    def get_location_details(self, lat: float, lon: float) -> dict:
        """Get detailed crime statistics for a location"""
        return self.viz.get_location_stats(lat, lon)
    
    def update_data(self, force: bool = False):
        """Update the crime data if needed"""
        self.viz.update_database(force=force)
    
    def get_trend_analysis(self, lat: float, lon: float) -> dict:
        """Get trend analysis for a location"""
        return self.viz.get_trend_analysis(lat, lon)

def create_crime_layer(resolution: int = 50):
    """Create the crime layer for the map"""
    layer = CrimeMapLayer(resolution=resolution)
    
    # Update data if needed
    layer.update_data()
    
    # Get heatmap data
    heatmap_data = layer.get_heatmap_data()
    
    if heatmap_data is None or heatmap_data.empty:
        print("No crime data available for map layer")
        return []
        
    return heatmap_data.to_dict('records')

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