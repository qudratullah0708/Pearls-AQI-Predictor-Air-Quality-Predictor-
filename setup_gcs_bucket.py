"""
GCS Bucket Setup Script
Creates the required GCS bucket for model artifacts manually
"""

import os
from google.cloud import storage
from google.oauth2 import service_account
from config import (
    GCP_PROJECT_ID,
    GCP_REGION,
    GCP_SERVICE_ACCOUNT_KEY_PATH,
    MODEL_ARTIFACTS_BUCKET
)

def create_bucket_manually():
    """Create GCS bucket manually with proper permissions"""
    print("🪣 Creating GCS bucket for model artifacts...")
    
    try:
        # Load credentials
        credentials = service_account.Credentials.from_service_account_file(
            GCP_SERVICE_ACCOUNT_KEY_PATH
        )
        
        # Initialize storage client
        storage_client = storage.Client(
            project=GCP_PROJECT_ID,
            credentials=credentials
        )
        
        bucket_name = MODEL_ARTIFACTS_BUCKET
        
        # Check if bucket already exists
        try:
            bucket = storage_client.bucket(bucket_name)
            bucket.reload()
            print(f"✅ Bucket already exists: gs://{bucket_name}")
            return True
        except Exception:
            print(f"📦 Creating new bucket: gs://{bucket_name}")
        
        # Create bucket
        bucket = storage_client.bucket(bucket_name)
        bucket.location = GCP_REGION
        
        # Set bucket properties
        bucket.storage_class = "STANDARD"
        bucket.lifecycle_rules = [
            {
                "action": {"type": "Delete"},
                "condition": {"age": 90}  # Delete files older than 90 days
            }
        ]
        
        # Create the bucket
        bucket = storage_client.create_bucket(bucket, location=GCP_REGION)
        
        print(f"✅ Successfully created bucket: gs://{bucket_name}")
        print(f"   📍 Location: {GCP_REGION}")
        print(f"   🗑️  Lifecycle: Auto-delete after 90 days")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating bucket: {e}")
        print(f"\n💡 Manual Setup Instructions:")
        print(f"1. Go to GCP Console → Cloud Storage → Buckets")
        print(f"2. Click 'Create bucket'")
        print(f"3. Name: {bucket_name}")
        print(f"4. Location: {GCP_REGION}")
        print(f"5. Storage class: Standard")
        print(f"6. Click 'Create'")
        return False

def check_bucket_permissions():
    """Check if service account has proper permissions"""
    print("🔐 Checking bucket permissions...")
    
    try:
        credentials = service_account.Credentials.from_service_account_file(
            GCP_SERVICE_ACCOUNT_KEY_PATH
        )
        
        storage_client = storage.Client(
            project=GCP_PROJECT_ID,
            credentials=credentials
        )
        
        bucket_name = MODEL_ARTIFACTS_BUCKET
        
        # Try to access bucket
        bucket = storage_client.bucket(bucket_name)
        bucket.reload()
        
        print(f"✅ Bucket access successful: gs://{bucket_name}")
        print(f"   📊 Bucket exists and accessible")
        print(f"   📁 Ready for model uploads")
        
        return True
        
    except Exception as e:
        print(f"❌ Bucket access failed: {e}")
        print(f"\n💡 Permission Fix Instructions:")
        print(f"1. Go to GCP Console → IAM & Admin → IAM")
        print(f"2. Find your service account: github-actions-aqi@...")
        print(f"3. Click 'Edit' (pencil icon)")
        print(f"4. Add role: 'Storage Admin'")
        print(f"5. Click 'Save'")
        return False

def test_model_upload():
    """Test uploading a small file to verify everything works"""
    print("🧪 Testing model upload...")
    
    try:
        credentials = service_account.Credentials.from_service_account_file(
            GCP_SERVICE_ACCOUNT_KEY_PATH
        )
        
        storage_client = storage.Client(
            project=GCP_PROJECT_ID,
            credentials=credentials
        )
        
        bucket_name = MODEL_ARTIFACTS_BUCKET
        
        # Create a test file
        test_content = "This is a test model file"
        test_filename = "test_model.txt"
        
        # Upload test file
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(f"test/{test_filename}")
        blob.upload_from_string(test_content)
        
        print(f"✅ Test upload successful!")
        print(f"   📁 File: gs://{bucket_name}/test/{test_filename}")
        
        # Clean up test file
        blob.delete()
        print(f"🗑️  Test file cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Test upload failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 GCS Bucket Setup for Model Registry")
    print("="*50)
    
    # Step 1: Create bucket
    bucket_created = create_bucket_manually()
    
    if bucket_created:
        # Step 2: Check permissions
        permissions_ok = check_bucket_permissions()
        
        if permissions_ok:
            # Step 3: Test upload
            upload_ok = test_model_upload()
            
            if upload_ok:
                print("\n🎉 GCS setup completed successfully!")
                print("✅ You can now run training_pipeline.py with Model Registry upload")
            else:
                print("\n⚠️  Upload test failed - check permissions")
        else:
            print("\n⚠️  Permission issues detected")
    else:
        print("\n⚠️  Bucket creation failed")
    
    print(f"\n📋 Next Steps:")
    print(f"1. Run: python training_pipeline.py")
    print(f"2. Check: python view_model_history.py")
    print(f"3. Test GitHub Actions workflow manually")

if __name__ == "__main__":
    main()
