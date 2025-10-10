"""
Migration script: Add day_of_week column to BigQuery table

This script adds the day_of_week column that was recently added to the 
feature pipeline but missing from the BigQuery table schema.

Usage:
    python scripts/add_day_of_week_column.py

Note: This is a one-time migration script to fix the schema mismatch.
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
    BIGQUERY_TABLE_ID,
)

def add_day_of_week_column():
    """Add day_of_week column to BigQuery table"""
    
    print("🚀 Adding day_of_week column to BigQuery table...")
    print("="*60)
    
    # Load service account credentials
    credentials = service_account.Credentials.from_service_account_file(
        GCP_SERVICE_ACCOUNT_KEY_PATH
    )
    
    # Initialize BigQuery client
    bq_client = bigquery.Client(project=GCP_PROJECT_ID, location=GCP_REGION, credentials=credentials)
    print(f"✅ BigQuery client initialized")
    
    # Get table reference
    table_path = f"{GCP_PROJECT_ID}.{BIGQUERY_DATASET_ID}.{BIGQUERY_TABLE_ID}"
    
    try:
        table = bq_client.get_table(table_path)
        print(f"✅ Found table: {table_path}")
    except Exception as e:
        print(f"❌ Error: Could not find table {table_path}: {e}")
        return False
    
    # Check current schema
    existing_columns = [field.name for field in table.schema]
    print(f"📋 Current columns: {existing_columns}")
    
    # Check if day_of_week column already exists
    if "day_of_week" in existing_columns:
        print("✅ day_of_week column already exists!")
        return True
    
    # Add the day_of_week column using SQL
    print("➕ Adding day_of_week column...")
    
    alter_sql = f"ALTER TABLE `{table_path}` ADD COLUMN day_of_week INTEGER"
    print(f"📝 Executing: {alter_sql}")
    
    try:
        job = bq_client.query(alter_sql)
        job.result()  # Wait for completion
        print(f"✅ Column added successfully!")
    except Exception as e:
        print(f"❌ Error adding column: {e}")
        return False
    
    # Populate the new column for existing data (if any)
    print("\n📝 Populating day_of_week for existing data...")
    
    # First, check if there's any data and get date ranges for partition filtering
    print("   🔍 Checking for existing data...")
    
    # Query to find date ranges of existing data (with partition filter)
    date_range_query = f"""
    SELECT 
        MIN(timestamp) as min_date,
        MAX(timestamp) as max_date,
        COUNT(*) as row_count
    FROM `{table_path}`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
    """
    
    try:
        date_result = bq_client.query(date_range_query).result()
        date_info = list(date_result)[0]
        row_count = date_info.row_count
        min_date = date_info.min_date
        max_date = date_info.max_date
        
        if row_count > 0:
            print(f"   Found {row_count} existing rows to update")
            print(f"   Date range: {min_date} to {max_date}")
            
            # Update query with partition filter - update recent data only
            # This respects BigQuery's partition elimination requirements
            update_query = f"""
            UPDATE `{table_path}` 
            SET day_of_week = EXTRACT(DAYOFWEEK FROM timestamp)
            WHERE day_of_week IS NULL 
            AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
            """
            
            try:
                job = bq_client.query(update_query)
                job.result()  # Wait for job to complete
                print(f"✅ Updated existing rows with day_of_week values (last 30 days)")
            except Exception as e:
                print(f"⚠️  Warning: Could not update existing data: {e}")
                print("   This is okay - new data will have day_of_week populated automatically")
        else:
            print("   No existing data to update (last 30 days)")
            
    except Exception as e:
        print(f"⚠️  Warning: Could not check existing data: {e}")
        print("   This is okay - new data will have day_of_week populated automatically")
    
    # Verify the final schema
    print("\n📋 Final schema verification...")
    updated_table = bq_client.get_table(table_path)
    final_columns = [field.name for field in updated_table.schema]
    
    if "day_of_week" in final_columns:
        print(f"✅ Migration complete!")
        print(f"   ✅ day_of_week column successfully added")
        print(f"   Total columns: {len(final_columns)}")
        return True
    else:
        print(f"❌ day_of_week column still missing after migration")
        return False

def main():
    """Main function"""
    try:
        success = add_day_of_week_column()
        
        if success:
            print("\n🎉 Schema update completed successfully!")
            print("✅ Your BigQuery table now has the day_of_week column")
            print("\nNext steps:")
            print("1. Run the feature pipeline again: python feature_pipeline.py")
            print("2. The pipeline should now work without schema errors")
        else:
            print("\n❌ Schema update failed!")
            exit(1)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
