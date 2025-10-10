<!-- ad032059-1f98-4ddb-8abc-3196534ba293 e8dc4872-00fb-4936-8f03-a800b36e6520 -->
# Vertex AI Feature Store & CI/CD Pipeline Implementation

## Phase 1: GCP Vertex AI Setup & Configuration (Programmatic Approach)

**Setup Hopsworks Account:**

- Create free account at app.hopsworks.ai
- Create new project (e.g., "aqi-predictor")
- Generate API key from Account Settings
- Note: Project name and API key needed for GitHub Secrets

**Project Configuration:**

- Create `config.py` for centralized configuration management
  - Environment variables for API keys (AQICN, Hopsworks)
  - Feature group definitions
  - Model parameters
- Update `requirements.txt` to include:
  - `hopsworks`
  - `hsfs` (Hopsworks Feature Store SDK)
  - `scikit-learn`
  - `mlflow` (for model tracking)

**Environment Variables Structure:**

```
AQICN_TOKEN - Air quality API token
HOPSWORKS_API_KEY - Hopsworks authentication
HOPSWORKS_PROJECT - Project name in Hopsworks
```

## Phase 2: Feature Pipeline Refactoring

**Modify `feature_pipeline.py`:**

- Keep existing functions: `fetch_data()`, `parse_features()`, `engineer_features()`
- Replace `save_to_store()` with `save_to_hopsworks()`
  - Initialize Hopsworks connection
  - Get or create Feature Group (versioned schema)
  - Insert features with timestamp as primary key
  - Handle duplicates and validation
- Add error handling and logging
- Remove CSV dependency (or keep as backup)

**Feature Group Schema:**

- Primary key: timestamp
- Event time: timestamp
- Features: city, aqi, dominant_pollutant, pm25, lat, lon, dew, humidity, pressure, temp, wind_speed, hour, day, month, year, aqi_change, aqi_roll3
- Version: 1 (can increment when schema changes)

## Phase 3: Training Pipeline Creation

**Create new `training_pipeline.py`:**

- Connect to Hopsworks and retrieve Feature Group
- Create Feature View (select relevant features for training)
- Split data: train (80%), test (20%) based on time
- Train multiple models:
  - Linear Regression (baseline)
  - Random Forest Regressor
  - XGBoost (if time permits)
- Evaluate using RMSE, MAE, R² metrics
- Save best model to Hopsworks Model Registry with:
  - Model artifacts (pickle/joblib)
  - Metrics metadata
  - Training timestamp
  - Feature importance plot

**Model Registry Structure:**

- Model name: "aqi_predictor"
- Version: auto-incremented
- Metrics: store in model schema
- Input schema: feature names and types

## Phase 4: GitHub Actions CI/CD

**Create `.github/workflows/feature_ingestion.yml`:**

- Trigger: Cron schedule (every hour: `0 * * * *`)
- Manual trigger option (workflow_dispatch)
- Steps:

  1. Checkout code
  2. Setup Python 3.12
  3. Install dependencies
  4. Run feature_pipeline.py
  5. Log results

- Secrets required: AQICN_TOKEN, HOPSWORKS_API_KEY, HOPSWORKS_PROJECT

**Create `.github/workflows/model_training.yml`:**

- Trigger: Cron schedule (daily at 2 AM: `0 2 * * *`)
- Manual trigger option
- Steps:

  1. Checkout code
  2. Setup Python 3.12
  3. Install dependencies
  4. Run training_pipeline.py
  5. Upload training logs as artifacts

- Uses same secrets as feature ingestion

**GitHub Secrets Setup:**

- Add all credentials to repository secrets
- Document in README how to configure

## Phase 5: Project Organization & Documentation

**Reorganize Project Structure:**

```
AQI/
├── .github/workflows/
│   ├── feature_ingestion.yml
│   └── model_training.yml
├── src/
│   ├── feature_pipeline.py
│   ├── training_pipeline.py
│   └── config.py
├── notebooks/ (optional - for EDA)
├── requirements.txt
├── README.md
└── .gitignore
```

**Update README.md:**

- Project overview and architecture diagram
- Setup instructions (Hopsworks account, GitHub secrets)
- How to run locally vs automated
- CI/CD pipeline explanation
- Results and metrics showcase

**Add `.gitignore`:**

- Ignore `.env` files
- Ignore local CSV backups
- Ignore model artifacts (stored in Hopsworks)
- Ignore Python cache files

## Phase 6: Testing & Validation

**Local Testing:**

- Test feature pipeline manually with Hopsworks
- Verify Feature Group appears in Hopsworks UI
- Test training pipeline and check Model Registry
- Confirm end-to-end flow works

**GitHub Actions Testing:**

- Trigger workflows manually first
- Verify GitHub Actions logs
- Check Hopsworks for new data after hourly run
- Check Model Registry after daily run
- Monitor for failures and add notifications

## Key Implementation Notes

**Best Practices:**

- Use try-except blocks for API calls
- Log all operations (print statements initially, proper logging later)
- Validate data quality before inserting to feature store
- Handle missing values in API response gracefully
- Add data validation (e.g., AQI should be 0-500)

**Security:**

- Never commit API keys
- Use GitHub Secrets for all credentials
- Add `.env.example` template file

**Scalability Considerations:**

- Feature Group supports incremental inserts (efficient for hourly updates)
- Model Registry supports versioning (can compare model performance over time)
- Can add more cities later by updating CITY list

**Portfolio Value:**

- Demonstrates MLOps knowledge (not just ML)
- Shows CI/CD automation skills
- Professional feature engineering practices
- Real-time data pipeline experience
- Cloud platform integration (Hopsworks)

### To-dos

- [ ] Setup Hopsworks account, create project, generate API key, and create config.py for environment management
- [ ] Update requirements.txt with hopsworks, hsfs, scikit-learn, and other ML dependencies
- [ ] Refactor feature_pipeline.py to integrate with Hopsworks Feature Store instead of CSV
- [ ] Create training_pipeline.py that reads from Hopsworks, trains models, and saves to Model Registry
- [ ] Create .github/workflows/feature_ingestion.yml for hourly automated data fetching
- [ ] Create .github/workflows/model_training.yml for daily automated model training
- [ ] Reorganize project structure, create proper folders, add .gitignore, and update documentation
- [ ] Test pipelines locally, then validate GitHub Actions workflows with manual triggers