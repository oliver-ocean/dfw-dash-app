from utils.helpers import fetch_with_fallback, generate_neighborhood_boundaries

@fetch_with_fallback(generate_neighborhood_boundaries)
def fetch_dallas_gis():
    raise NotImplementedError("Dallas GIS fetch not implemented")

@fetch_with_fallback(generate_neighborhood_boundaries)
def fetch_ftworth_gis():
    raise NotImplementedError("Ft Worth GIS fetch not implemented")

def get_combined_gis_data():
    geojson = fetch_dallas_gis()
    if geojson and "features" in geojson and geojson["features"]:
        return geojson
    return fetch_ftworth_gis()