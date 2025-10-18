"""
Test Feast feature store setup
"""
from feast import FeatureStore
import pandas as pd
from datetime import datetime

print("🧪 Testing Feast Feature Store...")
print("=" * 60)

# Initialize Feast
store = FeatureStore(repo_path="feature_repo")

# 1. List available feature views
print("\n📋 Available Feature Views:")
feature_views = store.list_feature_views()
for fv in feature_views:
    print(f"   - {fv.name}")

# 2. Check offline store (historical data)
print("\n📊 Offline Store (Historical Data):")
parquet_df = pd.read_parquet('feature_repo/data/aqi_features.parquet')
print(f"   Total records: {len(parquet_df)}")
print(f"   Date range: {parquet_df['timestamp'].min()} to {parquet_df['timestamp'].max()}")
print(f"   Columns: {len(parquet_df.columns)}")

# 3. Test online feature retrieval
print("\n🔥 Online Store (Real-time Serving):")
try:
    # Get latest features for Islamabad station
    entity_rows = [
        {"location_id": "islamabad_us_embassy"}
    ]
    
    # Retrieve specific features
    feature_vector = store.get_online_features(
        features=[
            "aqi_features:aqi",
            "aqi_features:pm25",
            "aqi_features:temp",
            "aqi_features:humidity",
        ],
        entity_rows=entity_rows
    ).to_dict()
    
    print("   ✅ Successfully retrieved online features!")
    print(f"   Sample: {feature_vector}")
    
except Exception as e:
    print(f"   ⚠️  Online features not available yet: {e}")

# 4. Test historical feature retrieval (for training)
print("\n📈 Historical Features (for Training):")
try:
    # Create entity dataframe with timestamps
    entity_df = pd.DataFrame({
        "location_id": ["islamabad_us_embassy"] * 5,
        "event_timestamp": pd.date_range("2025-10-12", periods=5, freq="1D")
    })
    
    # Get historical features
    training_df = store.get_historical_features(
        entity_df=entity_df,
        features=[
            "aqi_features:aqi",
            "aqi_features:pm25",
            "aqi_features:temp",
            "aqi_features:humidity",
            "aqi_features:pressure",
        ],
    ).to_df()
    
    print(f"   ✅ Retrieved {len(training_df)} historical records")
    print(f"\n   Sample data:")
    print(training_df.head())
    
except Exception as e:
    print(f"   ⚠️  Error: {e}")

print("\n" + "=" * 60)
print("🎉 Feast test complete!")