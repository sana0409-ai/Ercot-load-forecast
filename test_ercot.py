from gridstatus.ercot import Ercot
import pandas as pd
import sys
import traceback

ercot = Ercot()

try:
    df = ercot.get_load("latest")
    if df is None:
        print("ercot.get_load returned None")
        sys.exit(1)

    print("rows:", len(df))

    # show a compact sample
    print("\n--- head(10) ---")
    print(df.head(10).to_string())
    print("\n--- tail(10) ---")
    print(df.tail(10).to_string())

    print("\n--- dtypes ---")
    print(df.dtypes.to_string())

    # Try parsing Time to UTC
    if 'Time' in df.columns:
        try:
            df['Time_parsed'] = pd.to_datetime(df['Time'], errors='coerce', utc=True)
            print("\nTime parsed min/max:", df['Time_parsed'].min(), df['Time_parsed'].max())
            print("Time nulls:", df['Time_parsed'].isna().sum())
        except Exception as e:
            print("Time parse error:", e)

    if 'Load' in df.columns:
        df['Load'] = pd.to_numeric(df['Load'], errors='coerce')
        print("\nLoad min/max/nulls:", df['Load'].min(), df['Load'].max(), df['Load'].isna().sum())

except Exception as e:
    print("Exception calling Ercot:", e)
    traceback.print_exc()
