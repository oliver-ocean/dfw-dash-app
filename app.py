from flask import Flask, render_template
import folium
from folium.plugins import MarkerCluster

from fetch_modules.fetch_real_estate import get_combined_home_data
from fetch_modules.fetch_leasing import get_combined_leasing_data
from fetch_modules.fetch_traffic import get_combined_traffic_data

app = Flask(__name__)

@app.route("/")
def index():
    map_dfw = folium.Map(location=[32.9, -97.0], zoom_start=9)

    # Add Home Data
    home_data = get_combined_home_data()
    cluster = MarkerCluster(name="Homes").add_to(map_dfw)
    for _, row in home_data.iterrows():
        folium.CircleMarker(
            location=(row['Latitude'], row['Longitude']),
            radius=4,
            popup=f"{row['Neighborhood']}<br>Median: ${row['MedianHomePrice']:,.0f}",
            color="blue",
            fill=True
        ).add_to(cluster)

    # Add Leasing Data
    leasing_data = get_combined_leasing_data()
    for _, row in leasing_data.iterrows():
        folium.Marker(
            location=(row['Latitude'], row['Longitude']),
            popup=f"{row['Location']}<br>Lease: ${row['AvgLeasePrice']:.1f}/sqft",
            icon=folium.Icon(color="green")
        ).add_to(map_dfw)

    # Add Traffic Data
    traffic_data = get_combined_traffic_data()
    for _, row in traffic_data.iterrows():
        folium.Marker(
            location=(row['Latitude'], row['Longitude']),
            popup=f"{row['Road']}<br>Traffic: {row['AvgDailyTraffic']:,}",
            icon=folium.Icon(color="red")
        ).add_to(map_dfw)

    folium.LayerControl().add_to(map_dfw)
    map_dfw.save("templates/map.html")

    return render_template("map.html")

if __name__ == "__main__":
    app.run(debug=True)