"""
AQI Feature Pipeline - Hourly Data Ingestion
Fetches data from AQICN API and stores in BigQuery (syncs to Feature Store)
"""

import requests
import pandas as pd
import os
from feast_utils import append_features_to_offline_store, materialize_to_online_store
from config import (
    AQICN_TOKEN,
    CITY,
    AQICN_URL,
    validate_config
)

def fetch_data():
    """Fetch AQI data from AQICN API"""
    print("🌍 Fetching AQI data from API...")
    
    try:
        response = requests.get(AQICN_URL, timeout=30)
        print(f"📡 API Response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API call successful")
            return data
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network Error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return None

def parse_features(data):
    """Parse API response and extract features"""
    print("🔧 Parsing features from API response...")
    
    try:
        features = {}
        
        # Core AQI data
        features["timestamp"] = data["data"]["time"]["s"]
        features["city"] = data["data"]["city"]["name"]
        features["aqi"] = data["data"]["aqi"]
        features["dominant_pollutant"] = data["data"]["dominentpol"]
        
        # Air quality measurements
        iaqi = data["data"]["iaqi"]
        features["pm25"] = iaqi.get("pm25", {}).get("v")
        
        # Location data
        geo = data["data"]["city"]["geo"]
        features["latitude"] = geo[0]
        features["longitude"] = geo[1]
        
        # Weather data
        features["dew"] = iaqi.get("dew", {}).get("v")
        features["humidity"] = iaqi.get("h", {}).get("v")
        features["pressure"] = iaqi.get("p", {}).get("v")
        features["temp"] = iaqi.get("t", {}).get("v")
        features["wind_speed"] = iaqi.get("w", {}).get("v")
        
        # Convert to DataFrame
        df = pd.DataFrame([features])
        print(f"✅ Parsed {len(features)} features successfully")
        return df
        
    except KeyError as e:
        print(f"❌ Missing key in API response: {e}")
        return None
    except Exception as e:
        print(f"❌ Error parsing features: {e}")
        return None

def engineer_features(df):
    """Add derived features and time-based features"""
    print("⚙️ Engineering additional features...")
    
    try:
        # Convert timestamp to datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        # Time-based features
        df["hour"] = df["timestamp"].dt.hour
        df["day"] = df["timestamp"].dt.day
        df["month"] = df["timestamp"].dt.month
        df["year"] = df["timestamp"].dt.year
        df["day_of_week"] = df["timestamp"].dt.dayofweek  # 0=Monday, 6=Sunday
        
        # Create entity_id for Feature Store (ISO 8601 format)
        df["entity_id"] = df["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S")
        
        # Feature timestamp for Feature Store (same as timestamp)
        df["feature_timestamp"] = df["timestamp"]
        
        # Derived features (for now, set to None since we only have 1 row)
        # These will be calculated when we have historical data
        df["aqi_change"] = None  # Will be calculated in future runs
        df["aqi_roll3"] = None   # Will be calculated in future runs
        
        print("✅ Feature engineering completed")
        return df
        
    except Exception as e:
        print(f"❌ Error in feature engineering: {e}")
        return None


def save_to_feast(df):
    """Save feature to Feast feature store"""
    print("Saving to Feast Feature Store...")

    try:

        success = append_features_to_offline_store(df)
        if not success:
            print("❌ Failed to append features to offline store")
            return False
        
        success = materialize_to_online_store()
        if not success:
            print("❌ Failed to materialize features to online store")
            return False
        # materialize to online store
        print("✅ Features materialized to online store")
        return True
    
    except Exception as e:
        print(f"❌ Error saving to Feast Feature Store: {e}")
        return False

# def save_to_bigquery(df):
#     """Save features to BigQuery table (auto-syncs to Feature Store)"""
#     print("💾 Saving to BigQuery...")
    
#     try:
#         # Load service account credentials
#         credentials = service_account.Credentials.from_service_account_file(
#             GCP_SERVICE_ACCOUNT_KEY_PATH
#         )
        
#         # Initialize BigQuery client
#         bq_client = bigquery.Client(
#             project=GCP_PROJECT_ID, 
#             location=GCP_REGION, 
#             credentials=credentials
#         )
        
#         # Get table reference
#         table_path = f"{GCP_PROJECT_ID}.{BIGQUERY_DATASET_ID}.{BIGQUERY_TABLE_ID}"
#         table = bq_client.get_table(table_path)
        
#         # Check for existing timestamp to prevent duplicates
#         timestamp_str = df['timestamp'].iloc[0].strftime('%Y-%m-%d %H:%M:%S')
#         check_query = f"""
#         SELECT COUNT(*) as count 
#         FROM `{table_path}` 
#         WHERE timestamp = '{timestamp_str}'
#         """
#         try:
#             result = list(bq_client.query(check_query).result())
#             if result[0].count > 0:
#                 print(f"⚠️  Data for timestamp {timestamp_str} already exists - skipping insert")
#                 return True  # Not an error, just skip
#         except Exception as e:
#             print(f"⚠️  Could not check for duplicates: {e}")
#             # Continue anyway - might be table doesn't exist yet
        
#         # Prepare data for BigQuery
#         # Convert DataFrame to list of dictionaries with proper timestamp formatting
#         df_for_bigquery = df.copy()
        
#         # Convert Timestamp columns to ISO format strings for BigQuery
#         timestamp_columns = ['timestamp', 'feature_timestamp']
#         for col in timestamp_columns:
#             if col in df_for_bigquery.columns:
#                 df_for_bigquery[col] = df_for_bigquery[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        
#         # Convert DataFrame to list of dictionaries
#         rows_to_insert = df_for_bigquery.to_dict('records')
        
#         # Insert data
#         errors = bq_client.insert_rows_json(table, rows_to_insert)
        
#         if errors == []:
#             print("✅ Data saved to BigQuery successfully")
#             print(f"   📊 Table: {table_path}")
#             print(f"   📋 Rows inserted: {len(rows_to_insert)}")
#             print("   🔄 Auto-syncing to Feature Store...")
#             return True
#         else:
#             print(f"❌ Errors inserting data: {errors}")
#             return False
            
#     except Exception as e:
#         print(f"❌ Error saving to BigQuery: {e}")
#         return False

def main():
    """Main pipeline function"""
    print("🚀 Starting AQI Feature Pipeline")
    print("="*50)
    
    # Validate configuration
    try:
        validate_config()
        print("✅ Configuration validated")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return
    
    # Step 1: Fetch data from API
    data = fetch_data()
    if data is None:
        print("❌ Failed to fetch data from API")
        return
    
    # Step 2: Parse features
    df = parse_features(data)
    if df is None:
        print("❌ Failed to parse features")
        return
    
    # Step 3: Engineer features
    df = engineer_features(df)
    if df is None:
        print("❌ Failed to engineer features")
        return
    
    # Step 4: Save to Feast Feature Store
    success = save_to_feast(df)
    
    if success:
        print("\n🎉 Pipeline completed successfully!")
        print("✅ Data is now available in:")
        print("   📊 Feast Feature Store")
    else:
        print("\n❌ Pipeline failed!")

if __name__ == "__main__":
    main()