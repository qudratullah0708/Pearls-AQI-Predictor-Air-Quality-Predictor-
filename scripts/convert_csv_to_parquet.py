import pandas as pd
from pathlib import Path

print("Reading CSV file...")
df = pd.read_csv("data/exported_data_aqi_features.csv")

print("Parsing timestamps...")
df['timestamp'] = pd.to_datetime(df['timestamp'])

print("Adding location id Entity...")
df['location_id'] = "islamabad_us_embassy"

print(f"Data loaded successfully with {len(df)} rows and \n {df.columns.tolist()} columns \n and Date Range: {df['timestamp'].min()} to {df['timestamp'].max()}")

Path('feature_repo/data').mkdir(parents=True,exist_ok=True)

output_path = 'feature_repo/data/aqi_features.parquet'
print(f"Saving to {output_path}...")
df.to_parquet(output_path,index=False)
print("Converted CSV to Parquet successfully")

import os
file_size = os.path.getsize(output_path) / (1024 * 1024)
print(f"File size: {file_size:.2f} MB")
