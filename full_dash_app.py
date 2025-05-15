# Map
map_component = dl.Map(center=[32.78, -97.15], zoom=10, children=[
    dl.TileLayer(),
    traffic_layer,
    price_layer,
    crime_layer
], style={'width': '100%', 'height': '600px'}, id="main-map")

def create_traffic_markers():
    if traffic_grid.empty:
        return []
    
    markers = []
    for _, row in traffic_grid.iterrows():
        markers.append(
            dl.CircleMarker(
                center=[row['Latitude'], row['Longitude']],
                radius=4,  # Smaller radius
                color=get_color(row['color_scale']),
                fillOpacity=0.4,  # More transparent
                weight=1,
                children=dl.Tooltip(f"Traffic Level: {row['weighted_aadt']:,.0f} AADT")
            )
        )
    return markers

def create_crime_markers():
    if crime_grid.empty:
        return []
    
    markers = []
    for _, row in crime_grid.iterrows():
        markers.append(
            dl.CircleMarker(
                center=[row['Latitude'], row['Longitude']],
                radius=4,  # Smaller radius
                color=get_crime_color(row['color_scale']),
                fillOpacity=0.4,  # More transparent
                weight=1,
                children=dl.Tooltip(f"Crime Density: {row['weighted_crime']:.2f}")
            )
        )
    return markers 