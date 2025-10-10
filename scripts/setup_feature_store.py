import google.cloud.aiplatform as aiplatform
import google.cloud.bigquery as bigquery
from google.oauth2 import service_account
from config import (
    GCP_PROJECT_ID,
    GCP_REGION,
    GCP_SERVICE_ACCOUNT_KEY_PATH,
    BIGQUERY_DATASET_ID,
    BIGQUERY_TABLE_ID,
    FEATURE_GROUP_ID,
    FEATURE_GROUP_LOCATION,
    FEATURE_COLUMNS,
)

def setup_feature_store():
    # Load service account credentials
    credentials = service_account.Credentials.from_service_account_file(
        GCP_SERVICE_ACCOUNT_KEY_PATH
    )
    # Initialize Vertex AI with service account credentials
    aiplatform.init(project=GCP_PROJECT_ID, location=GCP_REGION, credentials=credentials)
    print(f"✅ Vertex AI initialized in project '{GCP_PROJECT_ID}' ({GCP_REGION})")
    
    # Initialize BigQuery client with credentials
    bigquery_client = bigquery.Client(project=GCP_PROJECT_ID, location=GCP_REGION, credentials=credentials)
    print(f"✅ BigQuery client initialized")
    
    # Verify BigQuery table exists and has correct schema
    table_path = f"{GCP_PROJECT_ID}.{BIGQUERY_DATASET_ID}.{BIGQUERY_TABLE_ID}"
    try:
        table = bigquery_client.get_table(table_path)
        print(f"✅ BigQuery table found: {table_path}")
    except Exception as e:
        print(f"❌ Error: Could not find table {table_path}: {e}")
        return
    
    # Validate schema (check for Feature Store required columns)
    actual_columns = [field.name for field in table.schema]
    print(f"📋 Table columns: {actual_columns}")
    
    # Check for Feature Store required columns
    required_columns = ["entity_id", "feature_timestamp"]
    missing_columns = [col for col in required_columns if col not in actual_columns]
    
    if missing_columns:
        print("⚠️  Missing Feature Store required columns:")
        print(f"   Missing: {missing_columns}")
        print("   Run: python migrate_add_feature_store_columns.py")
        return
    print("✅ All Feature Store required columns present")
    
    # TODO: Create Feature Group with BigQuery backend
    print("\n📋 Next: Feature Group creation will be implemented...")
    print("✅ BigQuery setup complete - ready for Feature Group creation!")
    
    # For now, just show success
    print(f"\n🎯 Setup Summary:")
    print(f"   📊 BigQuery Table: {table_path}")
    print(f"   📋 Schema Columns: {len(actual_columns)}")
    print(f"   ✅ Ready for Feature Group creation")

if __name__ == "__main__":
    setup_feature_store()





