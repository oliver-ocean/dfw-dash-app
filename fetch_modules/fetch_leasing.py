from utils.helpers import fetch_with_fallback, generate_leasing_data

@fetch_with_fallback(generate_leasing_data)
def fetch_costar_data():
    raise NotImplementedError("CoStar API not implemented")

@fetch_with_fallback(generate_leasing_data)
def fetch_cushman_data():
    raise NotImplementedError("Cushman API not implemented")

def get_combined_leasing_data():
    df = fetch_costar_data()
    if not df.empty:
        return df
    return fetch_cushman_data()