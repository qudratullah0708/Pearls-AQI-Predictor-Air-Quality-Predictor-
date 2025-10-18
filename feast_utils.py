"""
Feast Feature Store utility functions
Helper functions for AQI feature pipeline
"""
from feast import FeatureStore
import pandas as pd
from datetime import datetime
import os

FEAST_REPO_PATH = "feature_repo"
FEAST_DATA_FILE = "feature_repo/data/aqi_features.parquet"

def get_feast_store():
    """Initialize and return Feast FeatureStore"""
    return FeatureStore(repo_path=FEAST_REPO_PATH)

def append_features_to_offline_store(df):
    """
    Append new features to the Parquet file (offline store)
    
    Args:
        df: pandas DataFrame with new features
    """
    print("💾 Saving features to offline store...")
    
    # Ensure location_id exists
    if 'location_id' not in df.columns:
        df['location_id'] = 'islamabad_us_embassy'
    
    # Ensure timestamp is timezone-aware (UTC)
    if df['timestamp'].dt.tz is None:
        df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
    else:
        df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')
    
    # Convert feature_timestamp to string format for Parquet compatibility
    if 'feature_timestamp' in df.columns:
        df['feature_timestamp'] = df['feature_timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    
    # Append to existing parquet file
    if os.path.exists(FEAST_DATA_FILE):
        existing_df = pd.read_parquet(FEAST_DATA_FILE)
        combined_df = pd.concat([existing_df, df], ignore_index=True)
        combined_df = combined_df.drop_duplicates(subset=['timestamp'], keep='last')
        combined_df = combined_df.sort_values('timestamp')
    else:
        combined_df = df
    
    # Save back to parquet
    combined_df.to_parquet(FEAST_DATA_FILE, index=False)
    
    print(f"✅ Saved {len(df)} new records")
    print(f"   Total records in offline store: {len(combined_df)}")
    
    return True

def materialize_to_online_store(end_date=None):
    """
    Materialize features from offline → online store
    
    Args:
        end_date: datetime or None (uses current time if None)
    """
    print("🔄 Materializing features to online store...")
    
    store = get_feast_store()
    
    if end_date is None:
        end_date = datetime.now()
    
    try:
        # Materialize incrementally (only new data)
        store.materialize_incremental(end_date=end_date)
        print("✅ Features materialized to online store")
        return True
    except Exception as e:
        print(f"⚠️  Materialization error: {e}")
        return False

def get_historical_features_for_training(start_date, end_date):
    """
    Load historical features for model training
    
    Args:
        start_date: datetime - start of training period
        end_date: datetime - end of training period
        
    Returns:
        pandas DataFrame with features
    """
    print(f"📊 Loading historical features from Feast...")
    print(f"   Date range: {start_date} to {end_date}")
    
    # Read directly from parquet for training (faster than Feast API)
    df = pd.read_parquet(FEAST_DATA_FILE)
    
    # Ensure date parameters are timezone-aware (UTC)
    if start_date.tzinfo is None:
        start_date = pd.Timestamp(start_date).tz_localize('UTC')
    if end_date.tzinfo is None:
        end_date = pd.Timestamp(end_date).tz_localize('UTC')
    
    # Filter by date range
    df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
    
    print(f"✅ Loaded {len(df)} records")
    
    return df

def get_latest_features():
    """Get the most recent features from online store"""
    store = get_feast_store()
    
    entity_rows = [{"location_id": "islamabad_us_embassy"}]
    
    features = store.get_online_features(
        features=[
            "aqi_features:aqi",
            "aqi_features:pm25",
            "aqi_features:temp",
            "aqi_features:humidity",
            "aqi_features:pressure",
            "aqi_features:wind_speed",
        ],
        entity_rows=entity_rows
    ).to_dict()
    
    return features