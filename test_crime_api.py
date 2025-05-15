import sys
import os
import pandas as pd
import traceback

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from live_crime_data import fetch_crime_data

def test_crime_data():
    print("Testing crime data fetching...")
    print("Current working directory:", os.getcwd())
    try:
        print("\nAttempting to fetch crime data...")
        data = fetch_crime_data()
        
        if isinstance(data, pd.DataFrame):
            print("\nSuccessfully retrieved data!")
            print(f"Total records: {len(data)}")
            print("\nColumns available:")
            print(data.columns.tolist())
            if len(data) > 0:
                print("\nSample of first few records:")
                print(data.head(2).to_string())
            else:
                print("\nWarning: DataFrame is empty")
            return True
        else:
            print(f"\nError: Expected DataFrame but got {type(data)}")
            return False
    except Exception as e:
        print(f"\nTest failed with error: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_crime_data() 