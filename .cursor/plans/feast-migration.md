<!-- 419763a3-802a-4919-8159-f2db0826b0c7 a5cbff00-7167-43b2-a9dd-ba02413d2ad9 -->
# Feast Migration Plan: BigQuery to Open-Source Feature Store

## Overview

Migrate from paid GCP services (BigQuery + Vertex AI) to free, open-source Feast feature store with SQLite backend, enabling continued development without cloud costs.

## Phase 1: Setup Feast Environment

### 1.1 Install Feast Dependencies

Add to `requirements.txt`:

- `feast[sqlite]` - Feast with SQLite support
- Remove/comment out: `google-cloud-aiplatform`, `google-cloud-bigquery`, `google-cloud-storage`, `db-dtypes`, `pandas-gbq`

### 1.2 Initialize Feast Repository

Create `feature_store/` directory structure:

- `feature_repo/feature_store.yaml` - Feast configuration (SQLite backend)
- `feature_repo/features.py` - Feature definitions (AQI features schema)
- `feature_repo/data/` - SQLite database location

Key configuration:

```yaml
project: aqi_forecasting
provider: local
online_store:
  type: sqlite
  path: data/online_store.db
offline_store:
  type: file
entity_key_serialization_version: 2
```

### 1.3 Define Feature Views

In `feature_repo/features.py`, define:

- **Entity**: `aqi_reading` (identified by timestamp)
- **Feature View**: `aqi_features` with all 21 columns from CSV
- **Feature Sources**: File-based data source pointing to CSV

## Phase 2: Migrate Historical Data

### 2.1 Load Existing CSV Data

Use exported CSV: `data/exported data_aqi_features.csv` (140 records)

- Parse timestamp column correctly
- Ensure all 21 features are present
- Create entity column for Feast

### 2.2 Materialize Features to Feast

Run `feast materialize` to:

- Load historical data into SQLite offline store
- Populate online store for real-time serving
- Verify data integrity (140 records)

## Phase 3: Update Feature Pipeline

### 3.1 Modify `feature_pipeline.py`

Replace BigQuery operations with Feast operations:

**Remove** (lines 121-186):

- `save_to_bigquery()` function
- BigQuery client initialization
- Service account credentials for BigQuery

**Add**:

- `save_to_feast()` function
- Append new data to parquet/CSV file
- Run `feast materialize-incremental` to update feature store
- No GCP credentials needed

**Keep**:

- `fetch_data()` - AQICN API calls
- `parse_features()` - Feature extraction
- `engineer_features()` - Time-based features

### 3.2 Create Feast Helper Functions

New file: `feast_utils.py`

- `get_feast_client()` - Initialize Feast from feature_repo
- `write_features_to_source()` - Append to data source file
- `materialize_features()` - Update online/offline store
- `get_historical_features()` - Query for training

## Phase 4: Update Training Pipeline

### 4.1 Modify `training_pipeline.py`

Replace BigQuery data loading with Feast retrieval:

**Remove** (lines 240-287):

- `load_data_from_bigquery()` function
- BigQuery client initialization
- SQL queries

**Remove** (lines 152-238):

- `upload_to_model_registry()` - Vertex AI upload
- `upload_model_to_gcs()` - GCS operations
- `create_gcs_bucket()` - Bucket management
- `initialize_ai_platform()` - Vertex AI init

**Add**:

- `load_data_from_feast()` function using Feast SDK
- Query last 30 days of features
- Convert to pandas DataFrame (same format as before)

**Keep**:

- All model training logic (lines 422-492)
- Model evaluation (lines 494-575)
- Local model saving (lines 577-643)
- Feature importance plots (lines 645-693)

### 4.2 Simplify Model Storage

Enhance local model versioning:

- Save models with timestamps: `models/aqi_predictor_{horizon}_{timestamp}.pkl`
- Create `models/registry.json` for metadata tracking
- No cloud uploads needed

## Phase 5: Update Configuration

### 5.1 Modify `config.py`

Update configuration management:

**Remove/Comment**:

- All GCP-related variables (PROJECT_ID, REGION, SERVICE_ACCOUNT)
- BigQuery configuration (DATASET_ID, TABLE_ID)
- Vertex AI configuration (MODEL_REGISTRY, GCS paths)

**Add**:

- `FEAST_REPO_PATH = "feature_repo"`
- `FEAST_DATA_SOURCE = "data/aqi_features.parquet"`
- `LOCAL_MODEL_REGISTRY = "models/registry.json"`

**Keep**:

- AQICN API configuration
- Model hyperparameters
- Feature column definitions

### 5.2 Update Environment Variables

Modify `.env` file:

- Keep: `AQICN_TOKEN`
- Remove: `GCP_PROJECT_ID`, `GCP_REGION`, `GCP_SERVICE_ACCOUNT_KEY_PATH`

## Phase 6: Testing & Validation

### 6.1 Test Feature Pipeline

1. Run `python feature_pipeline.py`
2. Verify new data appends to parquet file
3. Check Feast materialization succeeds
4. Query online store to confirm data availability

### 6.2 Test Training Pipeline

1. Run `python training_pipeline.py`
2. Verify data loads from Feast (140+ records)
3. Check models train successfully
4. Confirm local model files created

### 6.3 Create Verification Script

New file: `scripts/verify_feast_setup.py`

- Check Feast repository validity
- Count features in offline store
- Test feature retrieval
- Validate data integrity

## Phase 7: Update Documentation

### 7.1 Update README.md

- Replace BigQuery/Vertex AI references with Feast
- Update architecture diagram (remove GCP services)
- Add Feast setup instructions
- Update Quick Start guide

### 7.2 Update CI/CD Notes

- Confirm GitHub Actions still work (no GCP secrets needed)
- Pipelines run locally or on GitHub runners
- No cloud costs incurred

## Key Benefits After Migration

✅ **Zero Cloud Costs**: Completely free, local operation

✅ **Faster Development**: No network latency to GCP

✅ **Learning Feast**: Industry-standard feature store

✅ **Portable**: Works on any machine, no cloud account needed

✅ **CI/CD Compatible**: GitHub Actions run without GCP credentials

## Migration Checklist

- [ ] Install Feast dependencies
- [ ] Initialize Feast repository with SQLite
- [ ] Define feature views and entities
- [ ] Load historical CSV into Feast
- [ ] Update feature_pipeline.py (remove BigQuery)
- [ ] Update training_pipeline.py (remove Vertex AI)
- [ ] Simplify config.py (remove GCP vars)
- [ ] Test feature pipeline end-to-end
- [ ] Test training pipeline end-to-end
- [ ] Update README documentation
- [ ] Verify CI/CD pipelines work

### To-dos

- [ ] Install Feast with SQLite support and update requirements.txt
- [ ] Initialize Feast repository with feature_store.yaml and features.py
- [ ] Load exported CSV data into Feast offline store
- [ ] Modify feature_pipeline.py to use Feast instead of BigQuery
- [ ] Modify training_pipeline.py to load from Feast and remove Vertex AI
- [ ] Update config.py to remove GCP dependencies and add Feast paths
- [ ] Create feast_utils.py helper module for common Feast operations
- [ ] Test both feature and training pipelines end-to-end
- [ ] Update README.md and documentation to reflect Feast migration