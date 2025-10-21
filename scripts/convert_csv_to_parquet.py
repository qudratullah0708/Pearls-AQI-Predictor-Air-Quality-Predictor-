import pandas as pd
from pathlib import Path
import os

print("Reading CSV file...")
csv_df = pd.read_csv("data/exported data_aqi_features.csv")

print("Parsing timestamps...")
csv_df['timestamp'] = pd.to_datetime(csv_df['timestamp'])

print("Adding location id Entity...")
csv_df['location_id'] = "islamabad_us_embassy"

print(f"CSV data loaded successfully with {len(csv_df)} rows")
print(f"Date Range: {csv_df['timestamp'].min()} to {csv_df['timestamp'].max()}")

# Ensure output directory exists
Path('feature_repo/data').mkdir(parents=True, exist_ok=True)
output_path = 'feature_repo/data/aqi_features.parquet'

# Check if parquet file already exists
if os.path.exists(output_path):
    print(f"\nExisting parquet file found at {output_path}")
    print("Loading existing data...")
    existing_df = pd.read_parquet(output_path)
    print(f"Existing records: {len(existing_df)}")
    print(f"Existing date range: {existing_df['timestamp'].min()} to {existing_df['timestamp'].max()}")
    
    # Merge dataframes, removing duplicates by timestamp (keep newer data)
    print("\nMerging data...")
    combined_df = pd.concat([existing_df, csv_df], ignore_index=True)
    
    # Remove duplicates based on timestamp, keeping the last occurrence (newer data)
    combined_df = combined_df.drop_duplicates(subset=['timestamp'], keep='last')
    combined_df = combined_df.sort_values('timestamp').reset_index(drop=True)
    
    print(f"Merge complete:")
    print(f"   Total records after merge: {len(combined_df)}")
    print(f"   New date range: {combined_df['timestamp'].min()} to {combined_df['timestamp'].max()}")
    print(f"   Records added: {len(combined_df) - len(existing_df)}")
    
    df = combined_df
else:
    print(f"\nNo existing parquet file found. Creating new one...")
    df = csv_df

print(f"\nSaving to {output_path}...")
df.to_parquet(output_path, index=False)
print("Converted CSV to Parquet successfully")

file_size = os.path.getsize(output_path) / (1024 * 1024)
print(f"File size: {file_size:.2f} MB")
print(f"Final record count: {len(df)}")
