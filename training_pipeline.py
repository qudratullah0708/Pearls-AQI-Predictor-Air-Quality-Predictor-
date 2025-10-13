"""
AQI Training Pipeline - Baseline Model Training for 3-Day Forecasting
Trains multiple models to predict AQI for 24h, 48h, and 72h ahead
"""

import pandas as pd
import numpy as np
import os
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from pathlib import Path
from google.cloud import bigquery
from google.oauth2 import service_account
from google.cloud import aiplatform
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
from config import (
    GCP_PROJECT_ID,
    GCP_REGION,
    GCP_SERVICE_ACCOUNT_KEY_PATH,
    BIGQUERY_DATASET_ID,
    BIGQUERY_TABLE_ID,
    MODEL_REGISTRY_NAME,
    MODEL_OUTPUT_DIR,
    EVALUATION_OUTPUT_DIR,
    PREDICTION_HORIZONS,
    TRAIN_TEST_SPLIT_RATIO,
    MODEL_CONFIGS,
    validate_config
)

def initialize_ai_platform():
    """Initialize Vertex AI with service account credentials"""
    print("🔧 Initializing Vertex AI...")
    
    try:
        credentials = service_account.Credentials.from_service_account_file(
            GCP_SERVICE_ACCOUNT_KEY_PATH
        )
        
        aiplatform.init(
            project=GCP_PROJECT_ID,
            location=GCP_REGION,
            credentials=credentials
        )
        
        print("✅ Vertex AI initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing Vertex AI: {e}")
        return False

def load_data_from_bigquery():
    """Load training data from BigQuery table"""
    print("📊 Loading data from BigQuery...")
    
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
        
        # Query data with partition filter (required for partitioned tables)
        table_path = f"{GCP_PROJECT_ID}.{BIGQUERY_DATASET_ID}.{BIGQUERY_TABLE_ID}"
        
        query = f"""
        SELECT 
            timestamp,
            hour,
            day_of_week,
            month,
            year,
            temp,
            humidity,
            pressure,
            wind_speed,
            dew,
            pm25,
            aqi
        FROM `{table_path}`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
        ORDER BY timestamp
        """
        
        df = bq_client.query(query).to_dataframe()
        
        print(f"✅ Loaded {len(df)} records from BigQuery")
        print(f"📅 Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        
        return df
        
    except Exception as e:
        print(f"❌ Error loading data from BigQuery: {e}")
        return None

def create_target_variables(df):
    """Create target variables for 24h, 48h, and 72h ahead predictions"""
    print("🎯 Creating target variables...")
    
    try:
        df = df.copy()
        
        # Sort by timestamp to ensure proper ordering
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        total_records = len(df)
        print(f"📊 Total records available: {total_records}")
        
        # Create target variables by shifting AQI values
        df['aqi_24h_ahead'] = df['aqi'].shift(-24)  # 24 hours ahead
        df['aqi_48h_ahead'] = df['aqi'].shift(-48)  # 48 hours ahead  
        df['aqi_72h_ahead'] = df['aqi'].shift(-72)  # 72 hours ahead
        
        # Count valid records for each horizon (DON'T drop them yet!)
        valid_24h = df['aqi_24h_ahead'].notna().sum()
        valid_48h = df['aqi_48h_ahead'].notna().sum()
        valid_72h = df['aqi_72h_ahead'].notna().sum()
        
        print(f"✅ Created target variables (handling each horizon independently)")
        print(f"📋 Available data for each horizon:")
        print(f"   - 24h ahead: {valid_24h} records (need 24h of future data)")
        print(f"   - 48h ahead: {valid_48h} records (need 48h of future data)")
        print(f"   - 72h ahead: {valid_72h} records (need 72h of future data)")
        
        # Provide recommendations based on data availability
        if valid_72h < 10:
            print(f"\n💡 Recommendation: You need at least {72 + 10} hours (~{(72 + 10) / 24:.1f} days) of data for 72h predictions")
            print(f"   Current data span: ~{total_records} hours (~{total_records / 24:.1f} days)")
        
        # Return full dataframe - we'll handle NaN values per horizon during training
        return df
        
    except Exception as e:
        print(f"❌ Error creating target variables: {e}")
        return None

def prepare_features_and_targets(df):
    """Prepare feature matrix and target variables"""
    print("🔧 Preparing features and targets...")
    
    try:
        # Select feature columns (exclude timestamp and target variables)
        feature_columns = [
            'hour', 'day_of_week', 'month', 'year',
            'temp', 'humidity', 'pressure', 'wind_speed', 'dew', 'pm25'
        ]
        
        # Check for missing values and handle them
        print("🔍 Checking for missing values...")
        missing_counts = df[feature_columns].isnull().sum()
        if missing_counts.sum() > 0:
            print("⚠️  Missing values found:")
            for col, count in missing_counts[missing_counts > 0].items():
                print(f"   {col}: {count} missing values")
            # Forward fill missing values (using new pandas syntax)
            df[feature_columns] = df[feature_columns].ffill()
            # If still NaN after forward fill, use backward fill
            df[feature_columns] = df[feature_columns].bfill()
            # If still NaN, fill with median for numeric columns
            numeric_cols = df[feature_columns].select_dtypes(include=[np.number]).columns
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
            print("✅ Missing values filled with forward/backward fill and median")
        
        # Create feature matrix
        X = df[feature_columns].copy()
        
        # Create target dictionary
        targets = {
            '24h': df['aqi_24h_ahead'].copy(),
            '48h': df['aqi_48h_ahead'].copy(),
            '72h': df['aqi_72h_ahead'].copy()
        }
        
        print(f"✅ Features prepared: {X.shape}")
        print(f"📋 Feature columns: {feature_columns}")
        
        return X, targets, feature_columns
        
    except Exception as e:
        print(f"❌ Error preparing features: {e}")
        return None, None, None

def split_data_temporally(X, targets):
    """Split data into train/test sets maintaining temporal order for each horizon"""
    print("✂️  Splitting data temporally (per horizon)...")
    
    try:
        train_targets = {}
        test_targets = {}
        X_train_dict = {}
        X_test_dict = {}
        
        for horizon, target in targets.items():
            print(f"   🎯 Processing {horizon} horizon...")
            
            # Find valid records for this horizon
            valid_mask = target.notna()
            valid_indices = target[valid_mask].index
            
            if len(valid_indices) == 0:
                print(f"      ⚠️  No valid data for {horizon}")
                continue
            
            # Sort by index to maintain temporal order
            valid_indices = sorted(valid_indices)
            
            # Split valid data temporally
            split_idx = int(len(valid_indices) * TRAIN_TEST_SPLIT_RATIO)
            train_indices = valid_indices[:split_idx]
            test_indices = valid_indices[split_idx:]
            
            # Extract data for this horizon
            X_train_dict[horizon] = X.loc[train_indices]
            X_test_dict[horizon] = X.loc[test_indices]
            train_targets[horizon] = target.loc[train_indices]
            test_targets[horizon] = target.loc[test_indices]
            
            print(f"      📊 {horizon}: {len(train_indices)} train, {len(test_indices)} test")
        
        print(f"✅ Data split completed per horizon")
        print(f"   📈 Split ratio: {TRAIN_TEST_SPLIT_RATIO:.1%}")
        
        return X_train_dict, X_test_dict, train_targets, test_targets
        
    except Exception as e:
        print(f"❌ Error splitting data: {e}")
        return None, None, None, None

def train_models(X_train_dict, train_targets, feature_columns):
    """Train models for all horizons"""
    print("🤖 Training models...")
    
    models = {}
    scalers = {}
    
    try:
        for horizon in ['24h', '48h', '72h']:
            print(f"\n🎯 Training models for {horizon} ahead prediction...")
            
            # Check if we have training data for this horizon
            if horizon not in X_train_dict or horizon not in train_targets:
                print(f"⚠️  No training data available for {horizon} - skipping")
                print(f"   💡 Need at least {int(horizon.replace('h', ''))} hours of future data")
                continue
            
            X_train_clean = X_train_dict[horizon]
            y_train_clean = train_targets[horizon]
            
            if len(X_train_clean) == 0:
                print(f"⚠️  No training data available for {horizon} - skipping")
                continue
            
            if len(X_train_clean) < 5:  # Reduced minimum for small datasets
                print(f"⚠️  Insufficient training data for {horizon}: {len(X_train_clean)} records (need at least 5)")
                print(f"   💡 This horizon will be skipped until more data is available")
                continue
                
            print(f"   📊 Training on {len(X_train_clean)} records")
            
            models[horizon] = {}
            scalers[horizon] = {}
            
            # Train each model type
            for model_name, config in MODEL_CONFIGS.items():
                print(f"   🔧 Training {model_name}...")
                
                try:
                    if model_name == "linear_regression":
                        model = LinearRegression()
                        # Scale features for linear regression
                        scaler = StandardScaler()
                        X_train_scaled = scaler.fit_transform(X_train_clean)
                        model.fit(X_train_scaled, y_train_clean)
                        scalers[horizon][model_name] = scaler
                        
                    elif model_name == "random_forest":
                        model = RandomForestRegressor(**config)
                        model.fit(X_train_clean, y_train_clean)
                        
                    elif model_name == "xgboost":
                        model = xgb.XGBRegressor(**config)
                        model.fit(X_train_clean, y_train_clean)
                    
                    models[horizon][model_name] = model
                    print(f"   ✅ {model_name} trained successfully")
                    
                except Exception as e:
                    print(f"   ❌ Error training {model_name}: {e}")
                    continue
        
        # Summary of trained models
        trained_models = sum(len(horizon_models) for horizon_models in models.values())
        print(f"\n✅ Model training completed: {trained_models} models trained across all horizons")
        
        return models, scalers
        
    except Exception as e:
        print(f"❌ Error in model training: {e}")
        return None, None

def evaluate_models(models, scalers, X_test_dict, test_targets, feature_columns):
    """Evaluate all models and return results"""
    print("📊 Evaluating models...")
    
    try:
        results = []
        
        for horizon in ['24h', '48h', '72h']:
            if horizon not in models or horizon not in X_test_dict or horizon not in test_targets:
                continue
                
            print(f"\n🎯 Evaluating {horizon} ahead predictions...")
            
            X_test_clean = X_test_dict[horizon]
            y_test_clean = test_targets[horizon]
            
            if len(X_test_clean) == 0:
                print(f"⚠️  No test data available for {horizon}")
                continue
            
            if len(X_test_clean) < 2:  # Reduced minimum for small datasets
                print(f"⚠️  Insufficient test data for {horizon}: {len(X_test_clean)} records (need at least 2)")
                continue
            
            print(f"   📊 Testing on {len(X_test_clean)} records")
            
            for model_name, model in models[horizon].items():
                try:
                    # Make predictions
                    if model_name == "linear_regression" and horizon in scalers and model_name in scalers[horizon]:
                        X_test_scaled = scalers[horizon][model_name].transform(X_test_clean)
                        y_pred = model.predict(X_test_scaled)
                    else:
                        y_pred = model.predict(X_test_clean)
                    
                    # Calculate metrics
                    mae = mean_absolute_error(y_test_clean, y_pred)
                    rmse = np.sqrt(mean_squared_error(y_test_clean, y_pred))
                    r2 = r2_score(y_test_clean, y_pred)
                    mape = np.mean(np.abs((y_test_clean - y_pred) / y_test_clean)) * 100
                    
                    result = {
                        'horizon': horizon,
                        'model': model_name,
                        'mae': mae,
                        'rmse': rmse,
                        'r2': r2,
                        'mape': mape,
                        'n_test_samples': len(y_test_clean),
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    results.append(result)
                    
                    print(f"   ✅ {model_name}: MAE={mae:.2f}, RMSE={rmse:.2f}, R²={r2:.3f}")
                    
                except Exception as e:
                    print(f"   ❌ Error evaluating {model_name}: {e}")
                    continue
        
        # Create results DataFrame
        results_df = pd.DataFrame(results)
        
        if len(results_df) > 0:
            print(f"\n📊 Evaluation Summary:")
            print(results_df[['horizon', 'model', 'mae', 'rmse', 'r2']].to_string(index=False))
            
            # Show best model for each horizon
            print(f"\n🏆 Best Models by Horizon:")
            for horizon in results_df['horizon'].unique():
                horizon_results = results_df[results_df['horizon'] == horizon]
                best_idx = horizon_results['mae'].idxmin()
                best_result = horizon_results.loc[best_idx]
                print(f"   {horizon}: {best_result['model']} (MAE: {best_result['mae']:.2f})")
        else:
            print("⚠️  No models were successfully evaluated")
        
        return results_df
        
    except Exception as e:
        print(f"❌ Error in model evaluation: {e}")
        return None

def save_best_models(models, scalers, results_df, feature_columns):
    """Save best model for each horizon locally and to Model Registry"""
    print("💾 Saving best models...")
    
    try:
        # Create output directories
        Path(MODEL_OUTPUT_DIR).mkdir(exist_ok=True)
        
        best_models = {}
        saved_models = []
        
        # Find best model for each horizon (lowest MAE)
        for horizon in ['24h', '48h', '72h']:
            horizon_results = results_df[results_df['horizon'] == horizon]
            
            if len(horizon_results) == 0:
                continue
                
            best_idx = horizon_results['mae'].idxmin()
            best_result = horizon_results.loc[best_idx]
            
            best_model_name = best_result['model']
            best_models[horizon] = {
                'model': models[horizon][best_model_name],
                'scaler': scalers[horizon].get(best_model_name),
                'model_name': best_model_name,
                'performance': best_result
            }
            
            # Save locally
            model_filename = f"{MODEL_OUTPUT_DIR}/aqi_predictor_{horizon}_{best_model_name}.pkl"
            joblib.dump(models[horizon][best_model_name], model_filename)
            
            # Save scaler if exists
            if scalers[horizon].get(best_model_name) is not None:
                scaler_filename = f"{MODEL_OUTPUT_DIR}/scaler_{horizon}_{best_model_name}.pkl"
                joblib.dump(scalers[horizon][best_model_name], scaler_filename)
            
            print(f"✅ Saved best {horizon} model: {best_model_name} (MAE: {best_result['mae']:.2f})")
            
            saved_models.append({
                'horizon': horizon,
                'model_name': best_model_name,
                'filename': model_filename,
                'performance': best_result
            })
        
        # Save model metadata
        metadata = {
            'feature_columns': feature_columns,
            'model_configs': MODEL_CONFIGS,
            'training_timestamp': datetime.now().isoformat(),
            'best_models': best_models
        }
        
        metadata_filename = f"{MODEL_OUTPUT_DIR}/model_metadata.json"
        import json
        with open(metadata_filename, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        print(f"✅ Model metadata saved to {metadata_filename}")
        
        return saved_models
        
    except Exception as e:
        print(f"❌ Error saving models: {e}")
        return None

def create_feature_importance_plots(models, feature_columns):
    """Create feature importance plots for tree-based models"""
    print("📊 Creating feature importance plots...")
    
    try:
        Path(EVALUATION_OUTPUT_DIR).mkdir(exist_ok=True)
        
        for horizon in ['24h', '48h', '72h']:
            if horizon not in models:
                continue
                
            for model_name, model in models[horizon].items():
                if model_name in ['random_forest', 'xgboost']:
                    try:
                        # Get feature importance
                        importance = model.feature_importances_
                        
                        # Create DataFrame
                        importance_df = pd.DataFrame({
                            'feature': feature_columns,
                            'importance': importance
                        }).sort_values('importance', ascending=True)
                        
                        # Create plot
                        plt.figure(figsize=(10, 6))
                        plt.barh(importance_df['feature'], importance_df['importance'])
                        plt.title(f'Feature Importance - {horizon} ahead ({model_name})')
                        plt.xlabel('Importance Score')
                        plt.tight_layout()
                        
                        # Save plot
                        plot_filename = f"{EVALUATION_OUTPUT_DIR}/feature_importance_{horizon}_{model_name}.png"
                        plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
                        plt.close()
                        
                        print(f"✅ Feature importance plot saved: {plot_filename}")
                        
                        # Print top 5 features
                        top_features = importance_df.tail(5)
                        print(f"   🏆 Top 5 features for {horizon} {model_name}:")
                        for _, row in top_features.iterrows():
                            print(f"      {row['feature']}: {row['importance']:.4f}")
                            
                    except Exception as e:
                        print(f"   ❌ Error creating importance plot for {horizon} {model_name}: {e}")
                        continue
        
    except Exception as e:
        print(f"❌ Error creating feature importance plots: {e}")

def save_evaluation_results(results_df):
    """Save evaluation results to CSV"""
    print("💾 Saving evaluation results...")
    
    try:
        Path(EVALUATION_OUTPUT_DIR).mkdir(exist_ok=True)
        
        # Save detailed results
        results_filename = f"{EVALUATION_OUTPUT_DIR}/model_evaluation_results.csv"
        results_df.to_csv(results_filename, index=False)
        print(f"✅ Evaluation results saved: {results_filename}")
        
        # Create performance tracking file
        tracking_filename = "model_performance_history.csv"
        
        # Load existing tracking if it exists
        if os.path.exists(tracking_filename):
            tracking_df = pd.read_csv(tracking_filename)
        else:
            tracking_df = pd.DataFrame()
        
        # Add new results
        tracking_df = pd.concat([tracking_df, results_df], ignore_index=True)
        tracking_df.to_csv(tracking_filename, index=False)
        
        print(f"✅ Performance tracking updated: {tracking_filename}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving evaluation results: {e}")
        return False

def main():
    """Main training pipeline function"""
    print("🚀 Starting AQI Training Pipeline")
    print("="*60)
    
    # Validate configuration
    try:
        validate_config()
        print("✅ Configuration validated")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return
    
    # Initialize Vertex AI
    if not initialize_ai_platform():
        print("⚠️  Continuing without Vertex AI initialization")
    
    # Step 1: Load data
    df = load_data_from_bigquery()
    if df is None:
        print("❌ Failed to load data from BigQuery")
        return
    
    # Step 2: Create target variables
    df = create_target_variables(df)
    if df is None:
        print("❌ Failed to create target variables")
        return
    
    # Step 3: Prepare features and targets
    X, targets, feature_columns = prepare_features_and_targets(df)
    if X is None:
        print("❌ Failed to prepare features")
        return
    
    # Step 4: Split data
    X_train_dict, X_test_dict, train_targets, test_targets = split_data_temporally(X, targets)
    if X_train_dict is None:
        print("❌ Failed to split data")
        return
    
    # Step 5: Train models
    models, scalers = train_models(X_train_dict, train_targets, feature_columns)
    if models is None:
        print("❌ Failed to train models")
        return
    
    # Step 6: Evaluate models
    results_df = evaluate_models(models, scalers, X_test_dict, test_targets, feature_columns)
    if results_df is None:
        print("❌ Failed to evaluate models")
        return
    
    # Step 7: Save best models (if any were trained)
    if len(results_df) > 0:
        saved_models = save_best_models(models, scalers, results_df, feature_columns)
        if saved_models is None:
            print("❌ Failed to save models")
            return
        
        # Step 8: Create feature importance plots
        create_feature_importance_plots(models, feature_columns)
        
        # Step 9: Save evaluation results
        save_evaluation_results(results_df)
        
        # Final summary
        print("\n🎉 Training Pipeline Completed Successfully!")
        print("="*60)
        print("📊 Summary:")
        print(f"   📈 Models trained: {len(results_df)} total")
        print(f"   🏆 Best models saved: {len(saved_models)}")
        print(f"   📁 Models directory: {MODEL_OUTPUT_DIR}/")
        print(f"   📊 Results directory: {EVALUATION_OUTPUT_DIR}/")
        print("\n✅ Ready for production deployment!")
    else:
        print("\n⚠️  Training Pipeline Completed with Limited Results")
        print("="*60)
        print("📊 Summary:")
        print("   📈 Models trained: 0 (insufficient data for training)")
        print("   💡 Data collection status:")
        print(f"      - Total records: {len(df)}")
        print(f"      - Data span: ~{len(df)} hours (~{len(df)/24:.1f} days)")
        print("   🚀 Next steps:")
        print("      - Continue collecting data hourly via CI/CD")
        print("      - Re-run training pipeline once you have 7+ days of data")
        print("      - 24h and 48h models should train once you have 3+ days")
        print("      - 72h models need 5+ days of data")
        print("\n✅ Pipeline is working correctly - just needs more data!")

if __name__ == "__main__":
    main()
