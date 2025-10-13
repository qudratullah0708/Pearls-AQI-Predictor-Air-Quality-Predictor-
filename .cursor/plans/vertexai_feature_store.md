<!-- ad032059-1f98-4ddb-8abc-3196534ba293 e8dc4872-00fb-4936-8f03-a800b36e6520 -->
# Historical Data Backfill & Training Pipeline Setup

## Phase 1: Historical Data Backfill Script

Create `backfill_historical_data.py` to populate BigQuery/Feature Store with past data:

**Key Components:**

- Generate timestamps for past date range (e.g., last 30-90 days)
- For each timestamp, fetch AQI data from AQICN API (if available)
- Reuse existing feature engineering logic from `feature_pipeline.py`
- Insert all historical records into BigQuery
- Handle rate limiting (API may have request limits)
- Progress tracking and error handling

**Implementation approach:**

- Accept date range as arguments (start_date, end_date)
- Iterate through dates/hours
- Sleep between requests to respect API rate limits
- Use batch inserts for efficiency
- Log progress and any failures

## Phase 2: Training Pipeline

Create `training_pipeline.py` to train and register ML models:

**Key Components:**

1. **Data Retrieval:**

- Query BigQuery with partition filter (last 30-90 days)
- Load features into pandas DataFrame
- Handle missing values and data quality checks

2. **Feature Preparation:**

- Time-based train/test split (e.g., 80/20)
- Select relevant features for model input
- Feature scaling/normalization if needed

3. **Model Training:**

- Start with simple models: LinearRegression, RandomForest, XGBoost
- Train on historical AQI prediction task
- Cross-validation for robust evaluation
- Hyperparameter tuning (optional for v1)

4. **Model Evaluation:**

- Metrics: RMSE, MAE, R² score
- Visualizations: actual vs predicted plots
- Save evaluation metrics

5. **Model Registry:**

- Save trained model to Google Cloud Storage
- Register model in Vertex AI Model Registry
- Version tracking and metadata

**Files to create:**

- `backfill_historical_data.py` - Historical data generation
- `training_pipeline.py` - Model training and registration
- `models/` directory - Local model storage (temporary)

**Files to update:**

- `config.py` - Add GCS bucket, model registry settings
- `requirements.txt` - Add scikit-learn, x

### To-dos

- [ ] Setup Hopsworks account, create project, generate API key, and create config.py for environment management
- [ ] Update requirements.txt with hopsworks, hsfs, scikit-learn, and other ML dependencies
- [ ] Refactor feature_pipeline.py to integrate with Hopsworks Feature Store instead of CSV
- [ ] Create training_pipeline.py that reads from Hopsworks, trains models, and saves to Model Registry
- [ ] Create .github/workflows/feature_ingestion.yml for hourly automated data fetching
- [ ] Create .github/workflows/model_training.yml for daily automated model training
- [ ] Reorganize project structure, create proper folders, add .gitignore, and update documentation
- [ ] Test pipelines locally, then validate GitHub Actions workflows with manual triggers