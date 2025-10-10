# Vertex AI Feature Store & CI/CD Pipeline Implementation

## Phase 1: Environment Setup & Dependencies

**Update Python Dependencies:**

- Add Google Cloud libraries to `requirements.txt`:
  - `google-cloud-aiplatform` - Vertex AI SDK
  - `google-cloud-bigquery` - BigQuery client
  - `db-dtypes` - BigQuery data type support
  - `pandas-gbq` - Pandas BigQuery integration

**Update Configuration:**

- Add BigQuery and Feature Store settings to `config.py`:
  - BigQuery dataset: `aqi_dataset`
  - BigQuery table: `aqi_features`
  - Feature Group ID: `aqi_readings`
  - Region: `us-central1`

## Phase 2: Feature Store Setup (One-time)

**Create Setup Script: `setup_feature_store.py`**

This script will:

1. Initialize Vertex AI with service account credentials
2. Verify BigQuery table exists and has correct schema
3. Create Feature Group programmatically with:

   - Source: BigQuery table `bq://PROJECT.aqi_dataset.aqi_features`
   - Entity ID: `timestamp` (TIMESTAMP type - proper for time-series)
   - Region: `us-central1`
   - Features: Auto-detected from BigQuery schema (18 features)

4. Verify Feature Group creation and list all features
5. Print setup summary

**Why programmatic:**

- UI limitation: Only shows STRING columns for entity ID
- SDK allows TIMESTAMP entity ID (correct for time-series)
- Infrastructure as code (reproducible, version-controlled)
- Professional approach used in production

**Run once to set up infrastructure**

## Phase 3: Feature Pipeline Refactoring

**Refactor `feature_pipeline.py` to write to BigQuery:**

Keep existing functions:

- `fetch_data()` - API calls to AQICN
- `parse_features()` - Extract features from JSON
- `engineer_features()` - Create time-based and derived features

Replace CSV storage with BigQuery:

- Remove `save_to_store()` function
- Add `save_to_bigquery()` function:
  - Initialize BigQuery client with service account
  - Convert DataFrame to BigQuery-compatible format
  - Handle TIMESTAMP conversion properly
  - Insert data to BigQuery table
  - Data automatically syncs to Feature Group
  - Add error handling and logging

**Data Flow:**

```
API → parse_features() → engineer_features() → BigQuery Table → Feature Group (auto-sync)
```

**Benefits:**

- Single write to BigQuery updates both BigQuery and Feature Group
- Can query BigQuery for analytics
- Feature Group optimized for ML training
- No manual sync needed

## Phase 4: Testing & Validation

**Local Testing:**

1. Test configuration: `python config.py`
2. Run setup (once): `python setup_feature_store.py`
3. Test data ingestion: `python feature_pipeline.py`
4. Verify in GCP Console:

   - BigQuery: Check `aqi_dataset.aqi_features` has new row
   - Vertex AI Feature Store: Check Feature Group shows data

5. Query data using BigQuery SQL to verify schema

**Validation Checks:**

- TIMESTAMP values are correct format
- All 18 features populated
- No duplicate timestamps
- Partitioning working (data in correct day partition)

## Phase 5: Training Pipeline Creation (Future)

**Create `training_pipeline.py`:**

- Read features from Feature Group (not BigQuery directly)
- Create training/test splits by time
- Train models (Linear Regression, Random Forest, XGBoost)
- Evaluate and save best model
- Store model in Vertex AI Model Registry

**Note:** This phase comes after data ingestion is working

## Phase 6: GitHub Actions CI/CD

**Create `.github/workflows/feature_ingestion.yml`:**

- Hourly schedule: `0 * * * *`
- Runs `feature_pipeline.py`
- Uses GitHub Secrets for credentials

**Create `.github/workflows/model_training.yml`:**

- Daily schedule: `0 2 * * *`
- Runs `training_pipeline.py`
- Uploads model artifacts

**GitHub Secrets needed:**

- `AQICN_TOKEN`
- `GCP_PROJECT_ID`
- `GCP_SERVICE_ACCOUNT_KEY` (JSON key as secret)

## Key Architecture Decisions

**Why BigQuery + Feature Group?**

- BigQuery: Data warehouse, SQL analytics, cost-effective storage
- Feature Group: ML-optimized reads, feature versioning, online serving
- Write to BigQuery → Feature Group auto-syncs
- Best of both worlds

**Why TIMESTAMP as Entity ID?**

- Time-series data: Each reading unique by time
- Proper data modeling (not using strings for timestamps)
- Enables time-travel queries
- Industry standard for time-series features

**Why Programmatic Setup?**

- UI limitations (only shows STRING for entity ID)
- Infrastructure as code (reproducible)
- Version controlled
- Professional approach
- Full SDK capabilities

## Project Structure (After Implementation)

```
AQI/
├── .github/workflows/
│   ├── feature_ingestion.yml (hourly)
│   └── model_training.yml (daily)
├── Pearls-AQI-Predictor-Air-Quality-Predictor-/
│   ├── config.py (centralized config)
│   ├── setup_feature_store.py (one-time setup)
│   ├── feature_pipeline.py (hourly ingestion)
│   ├── training_pipeline.py (daily training)
│   ├── requirements.txt (all dependencies)
│   ├── .env (local secrets)
│   ├── .gitignore (protect secrets)
│   └── README.md (documentation)
```

## Success Criteria

✅ Feature Group created with 18 features

✅ BigQuery table receives hourly data

✅ Feature Group auto-syncs from BigQuery

✅ Can query features via Feature Group SDK

✅ Pipeline runs without errors

✅ Data visible in GCP Console

✅ Ready for GitHub Actions automation