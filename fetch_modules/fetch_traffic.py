from utils.helpers import fetch_with_fallback, generate_traffic_data

@fetch_with_fallback(generate_traffic_data)
def fetch_txdot_data():
    raise NotImplementedError("TxDOT API not implemented")

@fetch_with_fallback(generate_traffic_data)
def fetch_nctcog_data():
    raise NotImplementedError("NCTCOG API not implemented")

def get_combined_traffic_data():
    df = fetch_txdot_data()
    if not df.empty:
        return df
    return fetch_nctcog_data()