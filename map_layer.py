import pandas as pd
import numpy as np
from typing import Dict, List
from crime_stats_db import CrimeStatsDB
from datetime import datetime, timedelta
from crime_visualization import CrimeVisualization
import dash_leaflet as dl
import json

class CrimeMapLayer:
    """Handles the crime data layer for the map"""
    
    def __init__(self, resolution: int = 100):
        """Initialize with visualization system"""
        self.viz = CrimeVisualization(grid_size=resolution)
        
    def get_heatmap_data(self):
        """Get current heatmap data for visualization"""
        data = self.viz.get_heatmap_data()
        if data is None or data.empty:
            return []
            
        # Convert to heatmap format
        heatmap_data = []
        for _, row in data.iterrows():
            # Scale risk score to intensity (0-1)
            intensity = row['risk_score']
            if not pd.isna(intensity):
                heatmap_data.append({
                    'lat': row['latitude'],
                    'lng': row['longitude'],
                    'intensity': float(intensity)
                })
        
        return dl.Heatmap(
            points=heatmap_data,
            options={
                'radius': 25,  # Size of each point's influence
                'blur': 15,    # Amount of blur
                'maxZoom': 20,
                'max': 1.0,    # Maximum intensity value
                'minOpacity': 0.3,  # Minimum opacity
                'gradient': {  # Custom color gradient
                    0.0: '#00ff00',  # Green for safe areas
                    0.4: '#ffff00',  # Yellow for moderate risk
                    0.6: '#ff9900',  # Orange for higher risk
                    0.8: '#ff0000',  # Red for high risk
                    1.0: '#990000'   # Dark red for highest risk
                }
            }
        )
    
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
    layer.update_data()
    return layer.get_heatmap_data()

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