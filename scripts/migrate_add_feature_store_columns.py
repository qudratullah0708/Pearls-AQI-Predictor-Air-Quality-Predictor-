"""
Migration script: Add required columns for Feature Store to BigQuery table

This script adds the required columns for Vertex AI Feature Store:
- entity_id (STRING): Unique entity identifier for Feature Store
- feature_timestamp (TIMESTAMP): Feature timestamp for Feature Store

Usage:
    python add_feature_store_columns.py

Note: This is a one-time migration script. Run this before creating
the Feature Group in Vertex AI Feature Store UI.

Created for AQI Predictor project - 10Pearls internship
"""

import os
from google.cloud import bigquery
from google.oauth2 import service_account
from config import (
    GCP_PROJECT_ID,
    GCP_REGION,
    GCP_SERVICE_ACCOUNT_KEY_PATH,
    BIGQUERY_DATASET_ID,
    BIGQUERY_TABLE_ID,
)

def add_feature_store_columns():
    """Add entity_id and feature_timestamp columns to BigQuery table"""
    
    print("🚀 Adding Feature Store required columns...")
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
    
    # Check what columns we need to add
    columns_to_add = []
    
    if "entity_id" not in existing_columns:
        columns_to_add.append(bigquery.SchemaField(
            name="entity_id",
            field_type="STRING",
            mode="REQUIRED",
            description="Unique entity ID for Feature Store"
        ))
        print("➕ Will add: entity_id (STRING)")
    
    if "feature_timestamp" not in existing_columns:
        columns_to_add.append(bigquery.SchemaField(
            name="feature_timestamp",
            field_type="TIMESTAMP",
            mode="REQUIRED",
            description="Feature timestamp for Feature Store"
        ))
        print("➕ Will add: feature_timestamp (TIMESTAMP)")
    
    if not columns_to_add:
        print("✅ All required columns already exist!")
        return True
    
    # Add the new columns using SQL (safer for existing tables)
    print(f"\n📝 Adding {len(columns_to_add)} columns using SQL...")
    
    # Build ALTER TABLE statements
    alter_statements = []
    
    for column in columns_to_add:
        # Add as NULLABLE first (BigQuery allows this)
        alter_sql = f"ALTER TABLE `{table_path}` ADD COLUMN {column.name} {column.field_type}"
        alter_statements.append(alter_sql)
        print(f"   📝 {alter_sql}")
    
    # Execute each ALTER TABLE statement
    for sql in alter_statements:
        try:
            job = bq_client.query(sql)
            job.result()  # Wait for completion
            print(f"   ✅ Executed: {sql}")
        except Exception as e:
            print(f"   ❌ Error executing {sql}: {e}")
            return False
    
    print(f"✅ All columns added successfully!")
    
    # Populate the new columns for existing data (if any)
    print("\n📝 Populating new columns for existing data...")
    
    # Check if table has any data
    count_query = f"SELECT COUNT(*) as row_count FROM `{table_path}`"
    count_result = bq_client.query(count_query).result()
    row_count = list(count_result)[0].row_count
    
    if row_count > 0:
        print(f"   Found {row_count} existing rows to update")
        
        # Update query to populate both new columns
        update_query = f"""
        UPDATE `{table_path}` 
        SET 
            entity_id = FORMAT_TIMESTAMP('%Y-%m-%dT%H:%M:%S', timestamp),
            feature_timestamp = timestamp
        WHERE entity_id IS NULL OR feature_timestamp IS NULL
        """
        
        try:
            job = bq_client.query(update_query)
            job.result()  # Wait for job to complete
            print(f"✅ Updated {row_count} existing rows")
        except Exception as e:
            print(f"⚠️  Warning: Could not update existing data: {e}")
            print("   This is okay if the table is empty")
    else:
        print("   No existing data to update")
    
    # Verify the final schema
    print("\n📋 Final schema verification...")
    updated_table = bq_client.get_table(table_path)
    final_columns = [field.name for field in updated_table.schema]
    
    print(f"✅ Migration complete!")
    print(f"   Total columns: {len(final_columns)}")
    
    # Check required columns
    required_columns = ["entity_id", "feature_timestamp"]
    missing_columns = [col for col in required_columns if col not in final_columns]
    
    if not missing_columns:
        print(f"✅ All Feature Store required columns present!")
        print(f"   ✅ entity_id: STRING")
        print(f"   ✅ feature_timestamp: TIMESTAMP")
        return True
    else:
        print(f"❌ Missing required columns: {missing_columns}")
        return False

def main():
    """Main function"""
    try:
        success = add_feature_store_columns()
        
        if success:
            print("\n🎉 Schema update completed successfully!")
            print("✅ Your table is now ready for Feature Store integration")
            print("\nNext steps:")
            print("1. Go back to Vertex AI Feature Store UI")
            print("2. Create Feature Group with:")
            print("   - Entity ID Column: entity_id")
            print("   - Feature Timestamp Column: feature_timestamp")
            print("3. Choose 'Include all columns from BigQuery table'")
        else:
            print("\n❌ Schema update failed!")
            exit(1)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
