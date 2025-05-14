from utils.helpers import fetch_with_fallback, generate_home_price_data

@fetch_with_fallback(generate_home_price_data)
def fetch_redfin_data():
    raise NotImplementedError("Redfin API not implemented")

@fetch_with_fallback(generate_home_price_data)
def fetch_zillow_data():
    raise NotImplementedError("Zillow API not implemented")

@fetch_with_fallback(generate_home_price_data)
def fetch_attom_data():
    raise NotImplementedError("ATTOM API not implemented")

def get_combined_home_data():
    df = fetch_redfin_data()
    if not df.empty:
        return df
    return fetch_zillow_data()