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

# Feast Feature Store Configuration
FEAST_REPO_PATH = "feature_repo"
FEAST_DATA_SOURCE = "feature_repo/data/aqi_features.parquet"
LOCAL_MODEL_REGISTRY = "models/registry.json"

# Model Training Configuration
MODEL_REGISTRY_NAME = "aqi-predictor"
MODEL_OUTPUT_DIR = "models"
EVALUATION_OUTPUT_DIR = "outputs"
PREDICTION_HORIZONS = [24, 48, 72]  # hours ahead
TRAIN_TEST_SPLIT_RATIO = 0.7

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

# # Feature Schema Definition
# FEATURE_COLUMNS = [
#     "timestamp",
#     "city",
#     "aqi",
#     "dominant_pollutant",
#     "pm25",
#     "latitude",
#     "longitude",
#     "dew",
#     "humidity",
#     "pressure",
#     "temp",
#     "wind_speed",
#     "hour",
#     "day",
#     "month",
#     "year",
#     "aqi_change",
#     "aqi_roll3"
# ]

# # BigQuery Schema Definition (for table creation)
# BIGQUERY_SCHEMA = [
#     {"name": "timestamp", "type": "TIMESTAMP", "mode": "REQUIRED"},
#     {"name": "city", "type": "STRING", "mode": "NULLABLE"},
#     {"name": "aqi", "type": "INTEGER", "mode": "REQUIRED"},
#     {"name": "dominant_pollutant", "type": "STRING", "mode": "NULLABLE"},
#     {"name": "pm25", "type": "FLOAT", "mode": "NULLABLE"},
#     {"name": "latitude", "type": "FLOAT", "mode": "NULLABLE"},
#     {"name": "longitude", "type": "FLOAT", "mode": "NULLABLE"},
#     {"name": "dew", "type": "FLOAT", "mode": "NULLABLE"},
#     {"name": "humidity", "type": "FLOAT", "mode": "NULLABLE"},
#     {"name": "pressure", "type": "FLOAT", "mode": "NULLABLE"},
#     {"name": "temp", "type": "FLOAT", "mode": "NULLABLE"},
#     {"name": "wind_speed", "type": "FLOAT", "mode": "NULLABLE"},
#     {"name": "hour", "type": "INTEGER", "mode": "NULLABLE"},
#     {"name": "day", "type": "INTEGER", "mode": "NULLABLE"},
#     {"name": "month", "type": "INTEGER", "mode": "NULLABLE"},
#     {"name": "year", "type": "INTEGER", "mode": "NULLABLE"},
#     {"name": "aqi_change", "type": "FLOAT", "mode": "NULLABLE"},
#     {"name": "aqi_roll3", "type": "FLOAT", "mode": "NULLABLE"},
#     {"name": "day_of_week", "type": "INTEGER", "mode": "NULLABLE"}
# ]

def validate_config():
    """Validate that all required configuration is present."""
    required_vars = {
        "AQICN_TOKEN": AQICN_TOKEN,
        # Remove GCP validation - not needed anymore!
    }
    
    missing = [key for key, value in required_vars.items() if not value]
    
    if missing:
        raise ValueError(
            f"❌ Missing required environment variables: {', '.join(missing)}\n"
            f"Please check your .env file!"
        )
    
    print("✅ Configuration validated successfully!")
    return True

def print_config_summary():
    """Print configuration summary (without sensitive data)."""
    print("\n" + "="*60)
    print("📋 AQI PREDICTOR CONFIGURATION")
    print("="*60)
    print(f"🌍 City: {CITY}")
    print(f"🔧 Feature Store: Feast (Local)")
    print(f"📁 Feast Repository: {FEAST_REPO_PATH}")
    print(f"📊 Data Source: {FEAST_DATA_SOURCE}")
    print(f"📦 Model Directory: {MODEL_OUTPUT_DIR}")
    print(f"📈 Prediction Horizons: {PREDICTION_HORIZONS} hours")
    print(f"🔑 API Token: {'✅ Configured' if AQICN_TOKEN else '❌ Missing'}")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        validate_config()
        print_config_summary()
    except Exception as e:
        print(f"\n❌ Configuration Error: {e}\n")
        exit(1)