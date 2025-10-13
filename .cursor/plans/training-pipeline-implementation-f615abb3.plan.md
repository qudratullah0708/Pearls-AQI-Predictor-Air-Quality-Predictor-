<!-- f615abb3-a781-4c30-86e5-75bb6cbdf0cb 2e6cd7e9-2f14-44b5-9772-decf0602cce4 -->
# Training Pipeline Implementation - Phase 5

## Overview

Create `training_pipeline.py` to train baseline models for 3-day AQI forecasting without lag features, using all 50 available records. This establishes a foundation for iterative improvement as data grows.

## Implementation Steps

### 1. Data Loading & Preparation

**File:** `training_pipeline.py`

**Read features from BigQuery:**

- Load all records from `aqi_dataset.aqi_features` table
- Select relevant features: time features (hour, day_of_week, month, year) + weather features (temp, humidity, pressure, wind_speed, dew, pm25)
- Handle missing values (forward fill for weather data)
- Sort by timestamp for temporal integrity

**Create target variables:**

- Since we don't have future data yet, we'll use a **simulation approach** for initial training
- Create targets by shifting AQI values: `aqi_24h_ahead`, `aqi_48h_ahead`, `aqi_72h_ahead`
- This reduces usable records (50 → 47 for 72h ahead) but enables immediate model development
- Document this limitation and plan to use real future data once available

### 2. Train/Test Split Strategy

**Time-based split (70/30):**

- Training: First 70% of records (chronologically)
- Testing: Last 30% of records
- Maintains temporal order (critical for time-series)
- No data leakage from future to past

**Validation:**

- Print split statistics (date ranges, record counts)
- Verify no overlap between train/test

### 3. Model Training - Three Separate Models

**Model 1: Linear Regression (Baseline)**

- Simplest model, establishes performance floor
- Fast training, interpretable coefficients
- Good for understanding feature relationships

**Model 2: Random Forest Regressor**

- Handles non-linear relationships
- Provides feature importance scores
- Robust to outliers

**Model 3: XGBoost Regressor**

- State-of-the-art gradient boosting
- Often best performance for tabular data
- Hyperparameters: `max_depth=3, n_estimators=100, learning_rate=0.1` (conservative for small data)

**For each horizon (24h, 48h, 72h):**

- Train all 3 model types
- Total: 9 models (3 types × 3 horizons)

### 4. Model Evaluation

**Metrics for each model:**

- **MAE** (Mean Absolute Error): Average prediction error in AQI units
- **RMSE** (Root Mean Squared Error): Penalizes large errors more
- **R²** (R-squared): Proportion of variance explained (0-1, higher better)
- **MAPE** (Mean Absolute Percentage Error): Error as percentage

**Comparison:**

- Create evaluation DataFrame comparing all 9 models
- Identify best model for each horizon
- Log results to console and save to CSV (`model_evaluation_results.csv`)

### 5. Model Registry Integration

**Save best model for each horizon to Vertex AI:**

- Use `aiplatform.Model.upload()` with proper metadata
- Model naming: `aqi-predictor-{horizon}h-{model_type}-v{version}`
- Include metadata:
  - Training date
  - Number of training records
  - Performance metrics (MAE, RMSE, R²)
  - Feature list
  - Model version

**Local backup:**

- Save models using `joblib` to `models/` directory
- Include model artifacts, feature names, and scaler objects

### 6. Feature Importance Analysis

**For tree-based models (Random Forest, XGBoost):**

- Extract feature importance scores
- Create visualization (bar chart)
- Save to `outputs/feature_importance_{horizon}h.png`
- Log top 5 most important features

**Learning insight:** Understand which features drive AQI predictions

### 7. Performance Tracking

**Create tracking file:** `model_performance_history.csv`

- Columns: timestamp, model_type, horizon, mae, rmse, r2, n_training_records, version
- Append new results each training run
- Enables tracking improvement over time

**Visualization:**

- Plot MAE vs. training data size over time
- Shows learning curve as data grows

## Configuration Updates

**Add to `config.py`:**

```python
# Model Training Configuration
MODEL_REGISTRY_NAME = "aqi-predictor"
MODEL_OUTPUT_DIR = "models"
EVALUATION_OUTPUT_DIR = "outputs"
PREDICTION_HORIZONS = [24, 48, 72]  # hours ahead
TRAIN_TEST_SPLIT_RATIO = 0.7
```

## Expected Outputs

After running `python training_pipeline.py`:

1. **Console logs:**

   - Data loading summary (50 records loaded)
   - Train/test split info (35 train, 15 test)
   - Training progress for each model
   - Evaluation metrics comparison table

2. **Files created:**

   - `models/aqi_predictor_24h_xgboost.pkl`
   - `models/aqi_predictor_48h_randomforest.pkl`
   - `models/aqi_predictor_72h_xgboost.pkl`
   - `outputs/model_evaluation_results.csv`
   - `outputs/feature_importance_24h.png`
   - `model_performance_history.csv`

3. **Vertex AI Model Registry:**

   - 3 models uploaded (best for each horizon)
   - Proper versioning and metadata

## Success Criteria

✅ Pipeline runs without errors on 50 records

✅ All 9 models train successfully

✅ Evaluation metrics calculated and logged

✅ Best models saved to Model Registry

✅ Feature importance analysis completed

✅ Performance tracking file created

✅ Ready for daily automation via GitHub Actions

## Future Enhancements (Week 2+)

Once you have 168+ records (7 days):

- Add lag features (aqi_lag_6h, aqi_lag_24h)
- Add rolling statistics (rolling_mean_24h, rolling_std_24h)
- Compare performance improvement
- Update models with richer features

## Learning Outcomes

By completing this phase, you'll learn:

- Time-series train/test splitting
- Multi-horizon forecasting approaches
- Model comparison and selection
- MLOps: Model Registry, versioning, tracking
- Feature importance interpretation
- Iterative model improvement strategy

### To-dos

- [ ] Add model training configuration constants to config.py
- [ ] Create training_pipeline.py with data loading from BigQuery
- [ ] Implement target variable creation (24h, 48h, 72h ahead AQI)
- [ ] Implement time-based train/test split (70/30)
- [ ] Train 3 model types (Linear Regression, Random Forest, XGBoost) for each horizon
- [ ] Calculate evaluation metrics (MAE, RMSE, R², MAPE) and compare models
- [ ] Save best models to Vertex AI Model Registry with metadata
- [ ] Extract and visualize feature importance for tree-based models
- [ ] Create performance tracking CSV to monitor improvement over time
- [ ] Test complete pipeline locally and verify all outputs