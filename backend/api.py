# backend/api.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from feast import FeatureStore
import joblib
import pandas as pd
import os
import json

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
store = FeatureStore(repo_path="feature_repo")

def load_active_models():
    """Load active models using _latest.pkl files for smart deployment"""
    try:
        models = {}
        
        # Model type mapping based on latest training
        model_types = {
            "24h": "xgboost",  # Based on recent training
            "48h": "random_forest",
            "72h": "random_forest"  # Currently using Random Forest
        }
        
        for horizon, model_type in model_types.items():
            # Try to load _latest.pkl first (active deployment)
            latest_path = f"models/aqi_predictor_{horizon}_{model_type}_latest.pkl"
            
            if os.path.exists(latest_path):
                models[horizon] = joblib.load(latest_path)
                print(f"✅ Loaded active {horizon} model from {latest_path}")
            else:
                # Fallback: try loading non-versioned file
                fallback_path = f"models/aqi_predictor_{horizon}_{model_type}.pkl"
                if os.path.exists(fallback_path):
                    models[horizon] = joblib.load(fallback_path)
                    print(f"⚠️  Fallback: Loaded {horizon} model from {fallback_path} (no _latest.pkl)")
                else:
                    print(f"❌ ERROR: No model found for {horizon} (tried {latest_path} and {fallback_path})")
        
        return models
    
    except Exception as e:
        print(f"❌ Error loading models: {e}")
        import traceback
        traceback.print_exc()
        return {}

# Load all trained models (using _latest.pkl for active deployment)
models = load_active_models()

@app.get("/current-aqi")
def get_current_aqi():
    """Get current AQI from online store"""
    features = store.get_online_features(
        features=[
            "aqi_features:aqi",
            "aqi_features:pm25",
            "aqi_features:dominant_pollutant",
            "aqi_features:temp",
            "aqi_features:humidity",
            "aqi_features:pressure",
            "aqi_features:wind_speed",
            "aqi_features:dew"
        ],
        entity_rows=[{"location_id": "islamabad_us_embassy"}]
    ).to_dict()
    return features

@app.get("/predict/{horizon}")
def predict_aqi(horizon: str):
    """Predict AQI for specific horizon (24h, 48h, 72h)"""
    # 1. Get latest features from online store
    features_df = store.get_online_features(
        features=[
            "aqi_features:temp",
            "aqi_features:humidity",
            "aqi_features:pressure",
            "aqi_features:wind_speed",
            "aqi_features:dew",
            "aqi_features:pm25",
            "aqi_features:hour",
            "aqi_features:day",
            "aqi_features:month",
            "aqi_features:year",
            "aqi_features:day_of_week",
            "aqi_features:aqi_change",
            "aqi_features:aqi_roll3"
        ],
        entity_rows=[{"location_id": "islamabad_us_embassy"}]
    ).to_df()
    
    # 2. Prepare features for prediction (match training pipeline)
    # Define the exact feature columns used during training
    training_features = [
        'hour', 'day_of_week', 'month', 'year',
        'temp', 'humidity', 'pressure', 'wind_speed', 'dew', 'pm25'
    ]
    
    # Drop entity columns and select only training features
    features = features_df[training_features].copy()
    
    # Convert all columns to numeric (handle any object dtypes)
    for col in features.columns:
        features[col] = pd.to_numeric(features[col], errors='coerce')
    
    # Handle any NaN values (forward fill, then backward fill, then median)
    features = features.ffill().bfill()
    for col in features.columns:
        if features[col].isna().any():
            features[col] = features[col].fillna(features[col].median())
    
    # 3. Predict using appropriate model
    model = models[horizon]
    prediction = model.predict(features)
    
    return {"horizon": horizon, "predicted_aqi": float(prediction[0])}

def get_latest_features_from_online_store():
    """Helper function to get latest features from online store"""
    features_df = store.get_online_features(
        features=[
            "aqi_features:temp",
            "aqi_features:humidity",
            "aqi_features:pressure",
            "aqi_features:wind_speed",
            "aqi_features:dew",
            "aqi_features:pm25",
            "aqi_features:hour",
            "aqi_features:day",
            "aqi_features:month",
            "aqi_features:year",
            "aqi_features:day_of_week",
            "aqi_features:aqi_change",
            "aqi_features:aqi_roll3"
        ],
        entity_rows=[{"location_id": "islamabad_us_embassy"}]
    ).to_df()
    
    # Prepare features for prediction (match training pipeline)
    training_features = [
        'hour', 'day_of_week', 'month', 'year',
        'temp', 'humidity', 'pressure', 'wind_speed', 'dew', 'pm25'
    ]
    
    # Drop entity columns and select only training features
    # Remove any entity columns that might be causing issues
    available_features = [col for col in training_features if col in features_df.columns]
    features = features_df[available_features].copy()
    
    # Convert all columns to numeric (handle any object dtypes)
    for col in features.columns:
        features[col] = pd.to_numeric(features[col], errors='coerce')
    
    # Handle any NaN values (forward fill, then backward fill, then median)
    features = features.ffill().bfill()
    for col in features.columns:
        if features[col].isna().any():
            features[col] = features[col].fillna(features[col].median())
    
    return features

@app.get("/predictions/all")
def get_all_predictions():
    """Get all predictions (24h, 48h, 72h) at once"""
    features = get_latest_features_from_online_store()
    
    return {
        "current_aqi": get_current_aqi(),
        "predictions": {
            "24h": float(models["24h"].predict(features)[0]),
            "48h": float(models["48h"].predict(features)[0]),
            "72h": float(models["72h"].predict(features)[0])
        }
    }

# ============ NEW PERFORMANCE TRACKING ENDPOINTS ============

@app.get("/model/info/{horizon}")
def get_model_info(horizon: str):
    """Get information about active model for a specific horizon"""
    try:
        deployment_metadata_path = "models/deployment_metadata.json"
        
        if not os.path.exists(deployment_metadata_path):
            return {"error": "Deployment metadata not found"}
        
        with open(deployment_metadata_path, 'r') as f:
            metadata = json.load(f)
        
        if horizon not in metadata.get('deployment_info', {}):
            return {"error": f"No model found for horizon {horizon}"}
        
        info = metadata['deployment_info'][horizon]
        
        return {
            "horizon": horizon,
            "model_type": info.get('metrics', {}).get('model_name', 'unknown'),
            "version": info.get('version', 'unknown'),
            "deployed": info.get('deployed', False),
            "deployed_at": info.get('deployment_timestamp', 'unknown'),
            "reason": info.get('reason', 'unknown'),
            "performance": {
                "rmse": info.get('metrics', {}).get('rmse'),
                "mae": info.get('metrics', {}).get('mae'),
                "r2": info.get('metrics', {}).get('r2'),
                "mape": info.get('metrics', {}).get('mape')
            }
        }
    
    except Exception as e:
        return {"error": str(e)}

@app.get("/model/performance/overview")
def get_performance_overview():
    """Get dashboard overview for all models"""
    try:
        from performance_db import get_best_model_for_horizon, get_performance_history
        
        deployment_metadata_path = "models/deployment_metadata.json"
        
        # Load deployment metadata
        deployment_info = {}
        if os.path.exists(deployment_metadata_path):
            with open(deployment_metadata_path, 'r') as f:
                metadata = json.load(f)
                deployment_info = metadata.get('deployment_info', {})
        
        results = {}
        
        for horizon in ['24h', '48h', '72h']:
            # Get best model from SQLite
            best_model_df = get_best_model_for_horizon(horizon)
            
            if len(best_model_df) == 0:
                results[horizon] = {"error": "No data available"}
                continue
            
            best_model = best_model_df.iloc[0]
            
            # Calculate trend (compare last 2 runs if available)
            history_df = get_performance_history(horizon, limit=2)
            trend = "stable"
            
            if len(history_df) >= 2:
                latest_rmse = history_df.iloc[0]['rmse']
                previous_rmse = history_df.iloc[1]['rmse']
                if latest_rmse < previous_rmse:
                    trend = "improving"
                elif latest_rmse > previous_rmse:
                    trend = "degrading"
            
            # Get deployment info
            dep_info = deployment_info.get(horizon, {})
            
            # Get total runs
            from performance_db import get_all_performance
            all_data = get_all_performance()
            total_runs = len(all_data[all_data['horizon'] == horizon])
            
            results[horizon] = {
                "current_rmse": float(best_model['rmse']),
                "current_mae": float(best_model['mae']),
                "current_r2": float(best_model['r2']),
                "trend": trend,
                "last_trained": best_model['timestamp'],
                "model_type": best_model['model'],
                "deployed": dep_info.get('deployed', False),
                "active_version": dep_info.get('version', 'unknown'),
                "total_runs": total_runs,
                "rmse": float(best_model['rmse']),
                "mae": float(best_model['mae']),
                "r2": float(best_model['r2']),
                "mape": float(best_model['mape'])
            }
        
        return results
    
    except Exception as e:
        return {"error": str(e)}

@app.get("/model/performance/{horizon}")
def get_performance_history_for_horizon(horizon: str, limit: int = 50):
    """Get historical performance data for a specific horizon"""
    try:
        from performance_db import get_performance_history
        
        # Get history from SQLite
        history_df = get_performance_history(horizon, limit=limit)
        
        if len(history_df) == 0:
            return {"error": f"No performance data found for horizon {horizon}"}
        
        # Convert to list of dicts for JSON response
        results = []
        for _, row in history_df.iterrows():
            results.append({
                "timestamp": row['timestamp'],
                "model": row['model'],
                "rmse": float(row['rmse']),
                "mae": float(row['mae']),
                "r2": float(row['r2']),
                "mape": float(row['mape']),
                "n_test_samples": int(row['n_test_samples']),
                "deployed": bool(row.get('deployed', 0))
            })
        
        return {
            "horizon": horizon,
            "count": len(results),
            "history": results
        }
    
    except Exception as e:
        return {"error": str(e)}

@app.get("/model/performance/history")
def get_full_performance_history():
    """Get complete performance history for all models"""
    try:
        from performance_db import get_all_performance
        
        df = get_all_performance()
        
        if len(df) == 0:
            return {"error": "No performance data found"}
        
        # Group by horizon
        results = {}
        for horizon in df['horizon'].unique():
            horizon_data = df[df['horizon'] == horizon].sort_values('timestamp', ascending=False)
            
            results[horizon] = []
            for _, row in horizon_data.iterrows():
                results[horizon].append({
                    "timestamp": row['timestamp'],
                    "model": row['model'],
                    "rmse": float(row['rmse']),
                    "mae": float(row['mae']),
                    "r2": float(row['r2']),
                    "mape": float(row['mape']),
                    "n_test_samples": int(row['n_test_samples']),
                    "deployed": bool(row.get('deployed', 0))
                })
        
        return results
    
    except Exception as e:
        return {"error": str(e)}

@app.get("/model/comparison/{horizon}")
def get_model_comparison(horizon: str):
    """Compare current vs previous model performance"""
    try:
        history_file = "model_performance_history.csv"
        deployment_metadata_path = "models/deployment_metadata.json"
        
        if not os.path.exists(history_file):
            return {"error": "Performance history not found"}
        
        df = pd.read_csv(history_file)
        
        # Filter by horizon and sort by timestamp
        horizon_data = df[df['horizon'] == horizon].sort_values('timestamp', ascending=False)
        
        if len(horizon_data) < 2:
            return {"error": "Insufficient data for comparison (need at least 2 training runs)"}
        
        # Get current and previous models
        current = horizon_data.iloc[0]
        previous = horizon_data.iloc[1]
        
        # Calculate improvement
        current_rmse = current['rmse']
        previous_rmse = previous['rmse']
        improvement_pct = ((previous_rmse - current_rmse) / previous_rmse) * 100
        
        # Load deployment info
        active_version = "unknown"
        if os.path.exists(deployment_metadata_path):
            with open(deployment_metadata_path, 'r') as f:
                metadata = json.load(f)
                if horizon in metadata.get('deployment_info', {}):
                    active_version = metadata['deployment_info'][horizon].get('version', 'unknown')
        
        return {
            "horizon": horizon,
            "current": {
                "timestamp": current['timestamp'],
                "model": current['model'],
                "rmse": float(current_rmse),
                "mae": float(current['mae']),
                "r2": float(current['r2']),
                "version": active_version
            },
            "previous": {
                "timestamp": previous['timestamp'],
                "model": previous['model'],
                "rmse": float(previous_rmse),
                "mae": float(previous['mae']),
                "r2": float(previous['r2'])
            },
            "comparison": {
                "rmse_change_pct": float(improvement_pct),
                "status": "improved" if improvement_pct > 0 else "degraded",
                "absolute_change": float(previous_rmse - current_rmse)
            }
        }
    
    except Exception as e:
        return {"error": str(e)}
