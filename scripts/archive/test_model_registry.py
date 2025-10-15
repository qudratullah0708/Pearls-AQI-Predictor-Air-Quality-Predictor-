"""
Test Model Registry Integration
Quick test to verify GCS bucket and Model Registry upload works
"""

import os
import sys
import joblib
import numpy as np
from datetime import datetime

# Add parent directory to path to import config
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from google.cloud import storage
from google.oauth2 import service_account
from google.cloud import aiplatform
from config import (
    GCP_PROJECT_ID,
    GCP_REGION,
    GCP_SERVICE_ACCOUNT_KEY_PATH,
    MODEL_ARTIFACTS_BUCKET,
    GCS_MODEL_PATH
)

def test_gcs_upload():
    """Test uploading a small file to GCS"""
    print("🧪 Testing GCS upload...")
    
    try:
        credentials = service_account.Credentials.from_service_account_file(
            GCP_SERVICE_ACCOUNT_KEY_PATH
        )
        
        storage_client = storage.Client(
            project=GCP_PROJECT_ID,
            credentials=credentials
        )
        
        # Create a test model file
        test_model = np.array([1, 2, 3, 4, 5])
        test_filename = "models/test_model.pkl"
        
        # Save locally first
        joblib.dump(test_model, test_filename)
        
        # Upload to GCS
        bucket = storage_client.bucket(MODEL_ARTIFACTS_BUCKET)
        blob = bucket.blob(f"{GCS_MODEL_PATH}/test_model.pkl")
        blob.upload_from_filename(test_filename)
        
        gcs_uri = f"gs://{MODEL_ARTIFACTS_BUCKET}/{GCS_MODEL_PATH}/test_model.pkl"
        print(f"✅ Test upload successful!")
        print(f"   📁 GCS URI: {gcs_uri}")
        
        # Clean up
        os.remove(test_filename)
        blob.delete()
        
        return True
        
    except Exception as e:
        print(f"❌ GCS upload test failed: {e}")
        return False

def test_model_registry_upload():
    """Test uploading a dummy model to Model Registry"""
    print("🧪 Testing Model Registry upload...")
    
    try:
        # Initialize Vertex AI
        credentials = service_account.Credentials.from_service_account_file(
            GCP_SERVICE_ACCOUNT_KEY_PATH
        )
        
        aiplatform.init(
            project=GCP_PROJECT_ID,
            location=GCP_REGION,
            credentials=credentials
        )
        
        # Create a dummy model
        dummy_model = np.array([1, 2, 3, 4, 5])
        model_filename = "models/dummy_test_model.pkl"
        
        # Save model locally
        joblib.dump(dummy_model, model_filename)
        
        # Upload to GCS first - create directory structure
        storage_client = storage.Client(
            project=GCP_PROJECT_ID,
            credentials=credentials
        )
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        gcs_model_dir = f"{GCS_MODEL_PATH}/test/dummy_model_v{timestamp}"
        gcs_model_path = f"{gcs_model_dir}/model.pkl"  # Standard filename
        
        bucket = storage_client.bucket(MODEL_ARTIFACTS_BUCKET)
        blob = bucket.blob(gcs_model_path)
        blob.upload_from_filename(model_filename)
        
        # Point to directory, not file
        gcs_uri = f"gs://{MODEL_ARTIFACTS_BUCKET}/{gcs_model_dir}/"
        
        # Upload to Model Registry
        display_name = f"test-aqi-model-{timestamp}"
        
        model = aiplatform.Model.upload(
            display_name=display_name,
            artifact_uri=gcs_uri,
            serving_container_image_uri="us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-0:latest",
            labels={'test': 'true', 'project': 'aqi-forecasting'},
            description="Test model for AQI prediction pipeline"
        )
        
        print(f"✅ Model Registry upload successful!")
        print(f"   📋 Model ID: {model.resource_name}")
        print(f"   🏷️  Display Name: {display_name}")
        
        # Clean up
        os.remove(model_filename)
        blob.delete()
        print(f"   🗑️  Cleaned up test files")
        
        return True
        
    except Exception as e:
        print(f"❌ Model Registry upload test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Model Registry Integration")
    print("="*50)
    
    # Test 1: GCS upload
    gcs_ok = test_gcs_upload()
    
    if gcs_ok:
        # Test 2: Model Registry upload
        registry_ok = test_model_registry_upload()
        
        if registry_ok:
            print("\n🎉 All tests passed!")
            print("✅ GCS bucket working")
            print("✅ Model Registry upload working")
            print("✅ Ready to run full training pipeline")
        else:
            print("\n⚠️  Model Registry test failed")
            print("💡 Check Vertex AI permissions")
    else:
        print("\n❌ GCS test failed")
        print("💡 Check Storage Admin permissions")
    
    print(f"\n📋 Next step: python training_pipeline.py")

if __name__ == "__main__":
    main()
