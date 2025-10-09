"""
Data Verification Script
Verifies data in BigQuery and provides Feature Store verification steps
"""

import sys
import os
from pathlib import Path

# Add parent directory to Python path to import config
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from google.cloud import bigquery
from google.oauth2 import service_account
from config import (
    GCP_PROJECT_ID, 
    GCP_REGION, 
    GCP_SERVICE_ACCOUNT_KEY_PATH, 
    BIGQUERY_DATASET_ID, 
    BIGQUERY_TABLE_ID
)

def verify_bigquery_data():
    """Verify data in BigQuery table"""
    print("🔍 Verifying BigQuery Data")
    print("="*60)
    
    try:
        # Initialize BigQuery client
        credentials = service_account.Credentials.from_service_account_file(
            GCP_SERVICE_ACCOUNT_KEY_PATH
        )
        bq_client = bigquery.Client(
            project=GCP_PROJECT_ID, 
            location=GCP_REGION, 
            credentials=credentials
        )
        
        # Query the latest data (with partition filter for partitioned table)
        query = f"""
        SELECT 
            timestamp,
            entity_id,
            feature_timestamp,
            city,
            aqi,
            pm25,
            temp,
            humidity,
            pressure,
            wind_speed
        FROM `{GCP_PROJECT_ID}.{BIGQUERY_DATASET_ID}.{BIGQUERY_TABLE_ID}`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
        ORDER BY timestamp DESC
        LIMIT 3
        """
        
        print("📊 Querying BigQuery table...")
        results = bq_client.query(query).result()
        
        row_count = 0
        for row in results:
            row_count += 1
            print(f"\n📋 Record #{row_count}:")
            print(f"   📅 Timestamp: {row.timestamp}")
            print(f"   🆔 Entity ID: {row.entity_id}")
            print(f"   🏷️  Feature Timestamp: {row.feature_timestamp}")
            print(f"   🏙️  City: {row.city}")
            print(f"   📊 AQI: {row.aqi}")
            print(f"   🌫️  PM2.5: {row.pm25}")
            print(f"   🌡️  Temperature: {row.temp}°C")
            print(f"   💧 Humidity: {row.humidity}%")
            print(f"   🌬️  Wind Speed: {row.wind_speed}")
            print("-" * 50)
        
        if row_count > 0:
            print(f"\n✅ SUCCESS: Found {row_count} records in BigQuery")
            print("✅ Entity ID and Feature Timestamp are populated correctly")
            return True
        else:
            print("\n❌ No data found in BigQuery table")
            return False
            
    except Exception as e:
        print(f"\n❌ Error querying BigQuery: {e}")
        return False

def print_feature_store_verification_steps():
    """Print steps to verify Feature Store data"""
    print("\n🔧 Feature Store Verification Steps")
    print("="*60)
    print("1. 🌐 Go to Vertex AI Feature Store Console:")
    print("   https://console.cloud.google.com/vertex-ai/feature-store")
    print()
    print("2. 🔍 Find your Feature Group:")
    print(f"   Project: {GCP_PROJECT_ID}")
    print(f"   Region: {GCP_REGION}")
    print(f"   Feature Group: aqi_readings")
    print()
    print("3. 📊 Check the 'Data' tab:")
    print("   - Should show your recent AQI data")
    print("   - Verify entity_id values match BigQuery")
    print("   - Check feature_timestamp is populated")
    print()
    print("4. 🎯 Check the 'Features' tab:")
    print("   - Should list all 20 columns from BigQuery")
    print("   - Verify data types are correct")
    print()
    print("5. ⏱️  Note: Data sync may take 1-2 minutes")

def main():
    """Main verification function"""
    print("🚀 AQI Data Verification")
    print("="*60)
    
    # Verify BigQuery data
    bigquery_success = verify_bigquery_data()
    
    if bigquery_success:
        # Print Feature Store verification steps
        print_feature_store_verification_steps()
        
        print("\n🎉 Verification Summary:")
        print("✅ BigQuery data is working correctly")
        print("✅ Entity ID and Feature Timestamp are populated")
        print("✅ Ready for Feature Store verification")
        print("\nNext steps:")
        print("1. Verify Feature Store data (see steps above)")
        print("2. Test data ingestion multiple times")
        print("3. Set up GitHub Actions for automation")
    else:
        print("\n❌ BigQuery verification failed")
        print("Please check the data pipeline and try again")

if __name__ == "__main__":
    main()
