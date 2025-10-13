"""
Test script for training pipeline - validates basic functionality
"""

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        import pandas as pd
        print("✅ pandas imported successfully")
    except ImportError as e:
        print(f"❌ pandas import failed: {e}")
        return False
    
    try:
        import numpy as np
        print("✅ numpy imported successfully")
    except ImportError as e:
        print(f"❌ numpy import failed: {e}")
        return False
    
    try:
        import sklearn
        print("✅ scikit-learn imported successfully")
    except ImportError as e:
        print(f"❌ scikit-learn import failed: {e}")
        return False
    
    try:
        import joblib
        print("✅ joblib imported successfully")
    except ImportError as e:
        print(f"❌ joblib import failed: {e}")
        return False
    
    # Test Google Cloud imports (might fail if not installed)
    try:
        from google.cloud import bigquery
        print("✅ google-cloud-bigquery imported successfully")
    except ImportError as e:
        print(f"⚠️  google-cloud-bigquery not available: {e}")
    
    try:
        from google.cloud import aiplatform
        print("✅ google-cloud-aiplatform imported successfully")
    except ImportError as e:
        print(f"⚠️  google-cloud-aiplatform not available: {e}")
    
    # Test XGBoost (might fail if not installed)
    try:
        import xgboost as xgb
        print("✅ xgboost imported successfully")
    except ImportError as e:
        print(f"⚠️  xgboost not available: {e}")
    
    # Test matplotlib (might fail if not installed)
    try:
        import matplotlib.pyplot as plt
        print("✅ matplotlib imported successfully")
    except ImportError as e:
        print(f"⚠️  matplotlib not available: {e}")
    
    return True

def test_config():
    """Test configuration loading"""
    print("\n🧪 Testing configuration...")
    
    try:
        from config import (
            GCP_PROJECT_ID,
            MODEL_OUTPUT_DIR,
            PREDICTION_HORIZONS,
            TRAIN_TEST_SPLIT_RATIO,
            MODEL_CONFIGS
        )
        print("✅ Configuration imported successfully")
        print(f"   📊 Prediction horizons: {PREDICTION_HORIZONS}")
        print(f"   📁 Model output dir: {MODEL_OUTPUT_DIR}")
        print(f"   📈 Train/test split: {TRAIN_TEST_SPLIT_RATIO}")
        print(f"   🤖 Model configs: {list(MODEL_CONFIGS.keys())}")
        return True
    except ImportError as e:
        print(f"❌ Configuration import failed: {e}")
        return False

def test_data_structures():
    """Test basic data structures and functions"""
    print("\n🧪 Testing data structures...")
    
    try:
        import pandas as pd
        import numpy as np
        
        # Create sample data
        dates = pd.date_range('2024-01-01', periods=50, freq='H')
        sample_data = pd.DataFrame({
            'timestamp': dates,
            'aqi': np.random.randint(50, 200, 50),
            'temp': np.random.uniform(15, 35, 50),
            'humidity': np.random.uniform(30, 90, 50)
        })
        
        print(f"✅ Sample data created: {sample_data.shape}")
        
        # Test target creation
        sample_data['aqi_24h_ahead'] = sample_data['aqi'].shift(-24)
        sample_data_clean = sample_data.dropna(subset=['aqi_24h_ahead'])
        
        print(f"✅ Target creation test: {len(sample_data_clean)} records after creating 24h target")
        
        # Test train/test split
        split_idx = int(len(sample_data_clean) * 0.7)
        train_data = sample_data_clean.iloc[:split_idx]
        test_data = sample_data_clean.iloc[split_idx:]
        
        print(f"✅ Train/test split test: {len(train_data)} train, {len(test_data)} test")
        
        return True
        
    except Exception as e:
        print(f"❌ Data structure test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Training Pipeline Test Suite")
    print("="*50)
    
    tests = [
        test_imports,
        test_config,
        test_data_structures
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Training pipeline is ready.")
        print("\n📋 Next steps:")
        print("1. Install missing dependencies: pip install -r requirements.txt")
        print("2. Run training pipeline: python training_pipeline.py")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        print("\n📋 To fix:")
        print("1. Install required dependencies: pip install -r requirements.txt")
        print("2. Check your .env file has all required variables")

if __name__ == "__main__":
    main()
