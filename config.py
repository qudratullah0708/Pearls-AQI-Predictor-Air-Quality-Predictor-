"""
Configuration management for AQI Predictor
Loads environment variables and validates configuration
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# AQICN API Configuration
AQICN_TOKEN = os.getenv("AQICN_TOKEN")
CITY = "islamabad"
AQICN_URL = f"http://api.waqi.info/feed/{CITY}/?token={AQICN_TOKEN}"

# GCP Configuration
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_REGION = os.getenv("GCP_REGION", "us-central1")
GCP_SERVICE_ACCOUNT_KEY_PATH = os.getenv("GCP_SERVICE_ACCOUNT_KEY_PATH")

# BigQuery Configuration
BIGQUERY_DATASET_ID = os.getenv("BIGQUERY_DATASET_ID", "aqi_dataset")
BIGQUERY_TABLE_ID = os.getenv("BIGQUERY_TABLE_ID", "aqi_features")
BIGQUERY_LOCATION = os.getenv("GCP_REGION", "us-central1")  # Use same region as GCP

# Vertex AI Feature Store Configuration
FEATURE_GROUP_ID = os.getenv("FEATURE_GROUP_ID", "aqi_readings")
FEATURE_GROUP_LOCATION = os.getenv("GCP_REGION", "us-central1")  # Use same region as GCP

# Model Training Configuration
MODEL_REGISTRY_NAME = "aqi-predictor"
MODEL_OUTPUT_DIR = "models"
EVALUATION_OUTPUT_DIR = "outputs"
PREDICTION_HORIZONS = [24, 48, 72]  # hours ahead
TRAIN_TEST_SPLIT_RATIO = 0.7

# Model Registry Configuration
MODEL_ARTIFACTS_BUCKET = f"{GCP_PROJECT_ID}-aqi-model-artifacts"
GCS_MODEL_PATH = "models"

# Model Hyperparameters (conservative for small datasets)
MODEL_CONFIGS = {
    "linear_regression": {},
    "random_forest": {
        "n_estimators": 50,
        "max_depth": 5,
        "random_state": 42
    },
    "xgboost": {
        "max_depth": 3,
        "n_estimators": 100,
        "learning_rate": 0.1,
        "random_state": 42
    }
}

# Feature Schema Definition
FEATURE_COLUMNS = [
    "timestamp",
    "city",
    "aqi",
    "dominant_pollutant",
    "pm25",
    "latitude",
    "longitude",
    "dew",
    "humidity",
    "pressure",
    "temp",
    "wind_speed",
    "hour",
    "day",
    "month",
    "year",
    "aqi_change",
    "aqi_roll3"
]

# BigQuery Schema Definition (for table creation)
BIGQUERY_SCHEMA = [
    {"name": "timestamp", "type": "TIMESTAMP", "mode": "REQUIRED"},
    {"name": "city", "type": "STRING", "mode": "NULLABLE"},
    {"name": "aqi", "type": "INTEGER", "mode": "REQUIRED"},
    {"name": "dominant_pollutant", "type": "STRING", "mode": "NULLABLE"},
    {"name": "pm25", "type": "FLOAT", "mode": "NULLABLE"},
    {"name": "latitude", "type": "FLOAT", "mode": "NULLABLE"},
    {"name": "longitude", "type": "FLOAT", "mode": "NULLABLE"},
    {"name": "dew", "type": "FLOAT", "mode": "NULLABLE"},
    {"name": "humidity", "type": "FLOAT", "mode": "NULLABLE"},
    {"name": "pressure", "type": "FLOAT", "mode": "NULLABLE"},
    {"name": "temp", "type": "FLOAT", "mode": "NULLABLE"},
    {"name": "wind_speed", "type": "FLOAT", "mode": "NULLABLE"},
    {"name": "hour", "type": "INTEGER", "mode": "NULLABLE"},
    {"name": "day", "type": "INTEGER", "mode": "NULLABLE"},
    {"name": "month", "type": "INTEGER", "mode": "NULLABLE"},
    {"name": "year", "type": "INTEGER", "mode": "NULLABLE"},
    {"name": "aqi_change", "type": "FLOAT", "mode": "NULLABLE"},
    {"name": "aqi_roll3", "type": "FLOAT", "mode": "NULLABLE"},
    {"name": "day_of_week", "type": "INTEGER", "mode": "NULLABLE"}
]

def validate_config():
    """Validate that all required configuration is present."""
    required_vars = {
        "AQICN_TOKEN": AQICN_TOKEN,
        "GCP_PROJECT_ID": GCP_PROJECT_ID,
        "GCP_SERVICE_ACCOUNT_KEY_PATH": GCP_SERVICE_ACCOUNT_KEY_PATH,
    }
    
    missing = [key for key, value in required_vars.items() if not value]
    
    if missing:
        raise ValueError(
            f"❌ Missing required environment variables: {', '.join(missing)}\n"
            f"Please check your .env file!"
        )
    
    # Check if service account key file exists
    key_path = Path(GCP_SERVICE_ACCOUNT_KEY_PATH)
    if not key_path.exists():
        raise FileNotFoundError(
            f"❌ Service account key not found at: {GCP_SERVICE_ACCOUNT_KEY_PATH}\n"
            f"Please make sure you moved the JSON key to the correct location!"
        )
    
    print("✅ Configuration validated successfully!")
    return True


def print_config_summary():
    """Print configuration summary (without sensitive data)."""
    print("\n" + "="*60)
    print("📋 AQI PREDICTOR CONFIGURATION")
    print("="*60)
    print(f"🌍 City: {CITY}")
    print(f"☁️  GCP Project: {GCP_PROJECT_ID}")
    print(f"📍 GCP Region: {GCP_REGION}")
    print(f"🗄️  BigQuery Dataset: {BIGQUERY_DATASET_ID}")
    print(f"📊 BigQuery Table: {BIGQUERY_TABLE_ID}")
    print(f"🔧 Feature Group: {FEATURE_GROUP_ID}")
    print(f"🔑 Service Account: {Path(GCP_SERVICE_ACCOUNT_KEY_PATH).name}")
    print(f"📦 Total Features: {len(FEATURE_COLUMNS)}")
    print(f"🏗️  BigQuery Schema Columns: {len(BIGQUERY_SCHEMA)}")
    print("="*60 + "\n")


def get_bigquery_table_path():
    """Get the full BigQuery table path."""
    return f"{GCP_PROJECT_ID}.{BIGQUERY_DATASET_ID}.{BIGQUERY_TABLE_ID}"


def get_bigquery_source_uri():
    """Get the BigQuery source URI for Feature Store."""
    return f"bq://{get_bigquery_table_path()}"


if __name__ == "__main__":
    try:
        validate_config()
        print_config_summary()
        print(f"📋 BigQuery Table Path: {get_bigquery_table_path()}")
        print(f"🔗 Feature Store Source: {get_bigquery_source_uri()}")
    except Exception as e:
        print(f"\n❌ Configuration Error: {e}\n")
        exit(1)