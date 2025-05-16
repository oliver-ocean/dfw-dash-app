import pandas as pd
import numpy as np
from typing import Dict, List
import dash_leaflet as dl
from live_traffic_data import fetch_traffic_data
from data_processing import calculate_weighted_traffic

class TrafficMapLayer:
    """Handles the traffic data layer for the map"""
    
    def __init__(self, resolution: int = 100):
        """Initialize with visualization system"""
        self.resolution = resolution
        self.data = None
        self.update_data()
        
    def update_data(self, force: bool = False):
        """Update the traffic data"""
        try:
            self.data = fetch_traffic_data()
        except Exception as e:
            print(f"Error updating traffic data: {str(e)}")
            print("Continuing with existing data")
    
    def get_heatmap_data(self):
        """Get current heatmap data for visualization"""
        if self.data is None or self.data.empty:
            return []
            
        # Calculate weighted traffic values
        grid_data = calculate_weighted_traffic(self.data, self.resolution)
        if grid_data.empty:
            return []
            
        # Convert to heatmap format
        heatmap_data = []
        for _, row in grid_data.iterrows():
            # Scale AADT to intensity (0-1)
            intensity = row['color_scale']  # Already normalized in calculate_weighted_traffic
            if not pd.isna(intensity):
                heatmap_data.append({
                    'lat': float(row['Latitude']),
                    'lng': float(row['Longitude']),
                    'intensity': float(intensity)
                })
        
        return dl.Heatmap(
            points=heatmap_data,
            options={
                'radius': 120,  # Size of each point's influence
                'blur': 80,    # Amount of blur
                'maxZoom': 20,
                'max': 1.0,    # Maximum intensity value
                'minOpacity': 0.05,  # Minimum opacity
                'gradient': {  # Custom color gradient
                    0.0: '#00ff00',  # Green for low traffic
                    0.4: '#ffff00',  # Yellow for moderate traffic
                    0.6: '#ff9900',  # Orange for busy traffic
                    0.8: '#ff0000',  # Red for heavy traffic
                    1.0: '#990000'   # Dark red for severe traffic
                }
            }
        )
    
    def get_location_details(self, lat: float, lon: float, radius: float = 0.02) -> dict:
        """Get traffic statistics for a specific location"""
        if self.data is None or self.data.empty:
            return None
            
        # Find nearby points
        distances = np.sqrt(
            (self.data['Latitude'] - lat)**2 + 
            (self.data['Longitude'] - lon)**2
        )
        nearby = self.data[distances <= radius].copy()
        
        if nearby.empty:
            return None
            
        # Calculate statistics
        stats = {
            'average_aadt': int(nearby['AADT'].mean()),
            'max_aadt': int(nearby['AADT'].max()),
            'nearby_roads': nearby['Road Name'].unique().tolist(),
            'point_count': len(nearby)
        }
        
        return stats

def create_traffic_layer(resolution: int = 50):
    """Create the traffic layer for the map"""
    layer = TrafficMapLayer(resolution=resolution)
    return layer.get_heatmap_data() 