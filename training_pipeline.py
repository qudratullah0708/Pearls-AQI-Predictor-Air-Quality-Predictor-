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
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

from feast_utils import get_historical_features_for_training

from config import (
    MODEL_OUTPUT_DIR,
    EVALUATION_OUTPUT_DIR,
    TRAIN_TEST_SPLIT_RATIO,
    MODEL_CONFIGS,
    DEPLOYMENT_METADATA_FILE,
    MODEL_VERSION_FORMAT,
    PERFORMANCE_HISTORY_FILE,
    validate_config
)
    
def load_data_from_feast():
    """Load training data from Feast feature store"""
    print("📊 Loading data from Feast...")
    
    try:
        # Load last 30 days of data for training
        from datetime import datetime, timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Use our Feast helper function
        df = get_historical_features_for_training(start_date, end_date)
        
        if len(df) == 0:
            print("⚠️  No data found in Feast for the specified date range")
            return None
        
        # Select relevant columns for training (same as before)
        training_columns = [
            'timestamp', 'hour', 'day_of_week', 'month', 'year',
            'temp', 'humidity', 'pressure', 'wind_speed', 'dew', 'pm25', 'aqi'
        ]
        
        # Check if all required columns exist
        missing_columns = [col for col in training_columns if col not in df.columns]
        if missing_columns:
            print(f"⚠️  Missing columns: {missing_columns}")
            # Use available columns
            available_columns = [col for col in training_columns if col in df.columns]
            df = df[available_columns]
        else:
            df = df[training_columns]
        
        print(f"✅ Loaded {len(df)} records from Feast")
        print(f"📅 Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"📋 Training columns: {list(df.columns)}")
        
        return df
        
    except Exception as e:
        print(f"❌ Error loading data from Feast: {e}")
        return None

def check_data_freshness(df):
    """Check if we have enough new data to warrant retraining"""
    print("🔍 Checking data freshness...")
    
    try:
        latest_timestamp = df['timestamp'].max()
        earliest_timestamp = df['timestamp'].min()
        
        hours_of_data = (latest_timestamp - earliest_timestamp).total_seconds() / 3600
        
        print(f"📊 Data freshness check:")
        print(f"   Latest: {latest_timestamp}")
        print(f"   Earliest: {earliest_timestamp}")
        print(f"   Hours of data: {hours_of_data:.1f}")
        
        # Require at least 72 hours (3 days) for meaningful training
        if hours_of_data < 72:
            print(f"⚠️  Insufficient data for training (need 72+ hours)")
            print(f"   💡 Current data span: {hours_of_data:.1f} hours")
            return False
        
        print(f"✅ Sufficient data for training: {hours_of_data:.1f} hours ({hours_of_data/24:.1f} days)")
        return True
        
    except Exception as e:
        print(f"❌ Error checking data freshness: {e}")
        return False

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

def should_deploy_model(horizon, model_name, new_rmse):
    """
    Decide whether to deploy a new model based on performance comparison.
    
    Args:
        horizon: Prediction horizon (24h, 48h, 72h)
        model_name: Model type (xgboost, random_forest, linear_regression)
        new_rmse: RMSE of the newly trained model
    
    Returns:
        bool: True if should deploy, False otherwise
    
    Logic:
        - If no previous model exists, always deploy (first model)
        - If new RMSE < previous best RMSE, deploy (improvement)
        - Otherwise, don't deploy (degradation)
    """
    try:
        import pandas as pd
        
        # Check if performance history exists
        if not os.path.exists(PERFORMANCE_HISTORY_FILE):
            print(f"✅ First model for {horizon} {model_name} - deploying automatically")
            return True
        
        # Load performance history
        history_df = pd.read_csv(PERFORMANCE_HISTORY_FILE)
        
        # Filter for this specific model (same horizon + model type)
        model_history = history_df[
            (history_df['horizon'] == horizon) & 
            (history_df['model'] == model_name)
        ].sort_values('timestamp', ascending=False)
        
        # If no previous models, deploy
        if len(model_history) == 0:
            print(f"✅ First {horizon} {model_name} model - deploying automatically")
            return True
        
        # Get previous best RMSE (most recent)
        previous_rmse = model_history.iloc[0]['rmse']
        
        # Calculate improvement percentage
        improvement_pct = ((previous_rmse - new_rmse) / previous_rmse) * 100
        
        # Decide based on performance
        if new_rmse < previous_rmse:
            print(f"✅ MODEL IMPROVED for {horizon} {model_name}")
            print(f"   Previous RMSE: {previous_rmse:.3f}")
            print(f"   New RMSE: {new_rmse:.3f}")
            print(f"   Improvement: {improvement_pct:.2f}%")
            print(f"   → DEPLOYING to production")
            return True
        else:
            print(f"⚠️  MODEL DEGRADED for {horizon} {model_name}")
            print(f"   Previous RMSE: {previous_rmse:.3f}")
            print(f"   New RMSE: {new_rmse:.3f}")
            print(f"   Degradation: {-improvement_pct:.2f}%")
            print(f"   → NOT deploying - keeping previous model active")
            return False
            
    except Exception as e:
        print(f"⚠️  Error checking deployment criteria: {e}")
        print(f"   Defaulting to: DEPLOY (safe fallback)")
        return True

def save_best_models(models, scalers, results_df, feature_columns):
    """Save best model for each horizon with versioning and smart deployment"""
    print("💾 Saving best models with versioning...")
    
    try:
        import json
        import shutil
        
        # Create output directories
        Path(MODEL_OUTPUT_DIR).mkdir(exist_ok=True)
        
        best_models = {}
        saved_models = []
        deployment_info = {}  # Track deployment decisions
        
        # Generate version timestamp
        version_timestamp = datetime.now().strftime(MODEL_VERSION_FORMAT)
        
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
            
            # Create versioned filename
            versioned_filename = f"{MODEL_OUTPUT_DIR}/aqi_predictor_{horizon}_{best_model_name}_{version_timestamp}.pkl"
            
            # ALWAYS save versioned model (for history)
            joblib.dump(models[horizon][best_model_name], versioned_filename)
            print(f"✅ Saved versioned {horizon} model: {best_model_name} v{version_timestamp}")
            
            # Save scaler if exists (also versioned)
            if scalers[horizon].get(best_model_name) is not None:
                versioned_scaler_filename = f"{MODEL_OUTPUT_DIR}/scaler_{horizon}_{best_model_name}_{version_timestamp}.pkl"
                joblib.dump(scalers[horizon][best_model_name], versioned_scaler_filename)
                
                # Also create _latest scaler
                latest_scaler_filename = f"{MODEL_OUTPUT_DIR}/scaler_{horizon}_{best_model_name}_latest.pkl"
            
            # Check if should deploy based on RMSE improvement
            should_deploy = should_deploy_model(horizon, best_model_name, best_result['rmse'])
            
            # Create _latest.pkl file (for API to load)
            latest_filename = f"{MODEL_OUTPUT_DIR}/aqi_predictor_{horizon}_{best_model_name}_latest.pkl"
            
            if should_deploy:
                # Deploy: Copy versioned model to _latest.pkl
                shutil.copy(versioned_filename, latest_filename)
                
                if scalers[horizon].get(best_model_name) is not None:
                    shutil.copy(versioned_scaler_filename, latest_scaler_filename)
                
                deployment_info[horizon] = {
                    'deployed': True,
                    'version': version_timestamp,
                    'deployment_timestamp': datetime.now().isoformat(),
                    'reason': 'RMSE improved',
                    'metrics': {
                        'rmse': float(best_result['rmse']),
                        'mae': float(best_result['mae']),
                        'r2': float(best_result['r2']),
                        'mape': float(best_result['mape'])
                    }
                }
                print(f"🚀 DEPLOYED {horizon} model to production")
            else:
                # Don't deploy: Keep existing _latest.pkl unchanged
                deployment_info[horizon] = {
                    'deployed': False,
                    'version': version_timestamp,
                    'deployment_timestamp': datetime.now().isoformat(),
                    'reason': 'RMSE degraded',
                    'metrics': {
                        'rmse': float(best_result['rmse']),
                        'mae': float(best_result['mae']),
                        'r2': float(best_result['r2']),
                        'mape': float(best_result['mape'])
                    }
                }
                print(f"⚠️  {horizon} model NOT deployed - keeping previous version active")
            
            saved_models.append({
                'horizon': horizon,
                'model_name': best_model_name,
                'versioned_filename': versioned_filename,
                'latest_filename': latest_filename,
                'deployed': should_deploy,
                'performance': best_result
            })
        
        # Save deployment metadata
        deployment_metadata = {
            'last_updated': datetime.now().isoformat(),
            'deployment_info': deployment_info,
            'training_config': {
                'feature_columns': feature_columns,
                'model_configs': MODEL_CONFIGS,
                'split_ratio': TRAIN_TEST_SPLIT_RATIO
            }
        }
        
        with open(DEPLOYMENT_METADATA_FILE, 'w') as f:
            json.dump(deployment_metadata, f, indent=2, default=str)
        
        print(f"✅ Deployment metadata saved to {DEPLOYMENT_METADATA_FILE}")
        
        # Also save model metadata (for compatibility)
        metadata = {
            'feature_columns': feature_columns,
            'model_configs': MODEL_CONFIGS,
            'training_timestamp': datetime.now().isoformat(),
            'best_models': best_models
        }
        
        metadata_filename = f"{MODEL_OUTPUT_DIR}/model_metadata.json"
        with open(metadata_filename, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        print(f"✅ Model metadata saved to {metadata_filename}")
        
        return saved_models
        
    except Exception as e:
        print(f"❌ Error saving models: {e}")
        import traceback
        traceback.print_exc()
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
    """Save evaluation results to SQLite database"""
    print("💾 Saving evaluation results...")
    
    try:
        from performance_db import save_performance_result
        
        Path(EVALUATION_OUTPUT_DIR).mkdir(exist_ok=True)
        
        # Save detailed results to CSV for backwards compatibility
        results_filename = f"{EVALUATION_OUTPUT_DIR}/model_evaluation_results.csv"
        results_df.to_csv(results_filename, index=False)
        print(f"✅ Evaluation results saved: {results_filename}")
        
        # Save to SQLite database
        for _, row in results_df.iterrows():
            result = {
                'timestamp': row['timestamp'],
                'horizon': row['horizon'],
                'model': row['model'],
                'mae': float(row['mae']),
                'rmse': float(row['rmse']),
                'r2': float(row['r2']),
                'mape': float(row['mape']),
                'n_test_samples': int(row['n_test_samples']),
                'deployed': 0  # Will be updated by deployment logic
            }
            save_performance_result(result)
        
        print(f"✅ Performance tracking saved to SQLite database")
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving evaluation results: {e}")
        import traceback
        traceback.print_exc()
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
    
    
        
    # Step 1: Load data
    df = load_data_from_feast()
    if df is None:
        print("❌ Failed to load data from Feast Feature Store")
        return
    
    # Step 1.5: Check data freshness
    if not check_data_freshness(df):
        print("⚠️  Insufficient data for training - exiting")
        print("💡 Continue collecting data hourly via CI/CD pipeline")
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
        
       
        
        # Step 9: Create feature importance plots
        create_feature_importance_plots(models, feature_columns)
        
        # Step 10: Save evaluation results
        save_evaluation_results(results_df)
        
        # Final summary
        print("\n🎉 Training Pipeline Completed Successfully!")
        print("="*60)
        print("📊 Summary:")
        print(f"   📈 Models trained: {len(results_df)} total")
        print(f"   🏆 Best models saved: {len(saved_models)}")
        print(f"    Models directory: {MODEL_OUTPUT_DIR}/")
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
