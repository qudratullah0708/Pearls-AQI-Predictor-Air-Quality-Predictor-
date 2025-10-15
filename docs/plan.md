# Vertex AI Feature Store & CI/CD Pipeline Implementation

## 🎯 **Learning Objectives Overview**

This project demonstrates mastery of modern MLOps practices through hands-on implementation of a production-ready AQI forecasting system.

### **Key Learning Areas:**
- **Cloud-Native ML Architecture**: GCP, Vertex AI, BigQuery integration
- **Data Engineering**: ETL pipelines, feature stores, data quality
- **Machine Learning**: Time-series forecasting, model evaluation
- **MLOps**: Model registry, containerization, CI/CD automation
- **Software Engineering**: Clean code, testing, documentation

## ✅ Phase 1: Environment Setup & Dependencies - COMPLETED

**🎓 Learning Goal**: Master cloud-native ML infrastructure setup

**✅ Skills Developed:**
- GCP project configuration and service integration
- Authentication and security best practices
- Infrastructure as code principles
- Dependency management for ML projects

**✅ Python Dependencies Updated:**

- Added Google Cloud libraries to `requirements.txt`:
  - `google-cloud-aiplatform` - Vertex AI SDK
  - `google-cloud-bigquery` - BigQuery client
  - `db-dtypes` - BigQuery data type support
  - `pandas-gbq` - Pandas BigQuery integration

**✅ Configuration Updated:**

- Updated `config.py` with BigQuery and Feature Store settings:
  - BigQuery dataset: `aqi_dataset`
  - BigQuery table: `aqi_features`
  - Feature Group ID: `aqi_readings`
  - Region: `us-central1`
  - Service account authentication configured

## ✅ Phase 2: Feature Store Setup (One-time) - COMPLETED

**✅ Setup Script Created: `setup_feature_store.py`**

**✅ Implementation Completed:**

1. ✅ Initialize Vertex AI with service account credentials
2. ✅ Verify BigQuery table exists and has correct schema
3. ✅ Create Feature Group programmatically with:
   - Source: BigQuery table `bq://PROJECT.aqi_dataset.aqi_features`
   - Entity ID: `entity_id` (STRING type for Feature Store compatibility)
   - Feature Timestamp: `feature_timestamp` (TIMESTAMP type)
   - Region: `us-central1`
   - Features: Auto-detected from BigQuery schema (20+ features)

4. ✅ Verify Feature Group creation and list all features
5. ✅ Print setup summary and verification steps

**✅ Architecture Decision - Why programmatic:**
- UI limitation: Only shows STRING columns for entity ID
- SDK allows proper Feature Store integration
- Infrastructure as code (reproducible, version-controlled)
- Professional approach used in production
- Better error handling and logging

## ✅ Phase 3: Feature Pipeline Refactoring - COMPLETED

**✅ Refactored `feature_pipeline.py` to write to BigQuery:**

**✅ Existing Functions Enhanced:**
- `fetch_data()` - API calls to AQICN with improved error handling
- `parse_features()` - Extract features from JSON with validation
- `engineer_features()` - Create time-based and derived features including:
  - Time features: hour, day, month, year, day_of_week
  - Feature Store fields: entity_id, feature_timestamp
  - Derived features: aqi_change, aqi_roll3 (for future use)

**✅ BigQuery Integration Implemented:**
- ✅ `save_to_bigquery()` function with:
  - BigQuery client initialization with service account
  - DataFrame to BigQuery-compatible format conversion
  - Proper TIMESTAMP conversion and formatting
  - Data insertion to BigQuery table with duplicate prevention
  - Automatic Feature Group sync
  - Comprehensive error handling and logging

**✅ Data Flow Implemented:**
```
API → parse_features() → engineer_features() → BigQuery Table → Feature Group (auto-sync)
```

**✅ Benefits Achieved:**
- Single write to BigQuery updates both BigQuery and Feature Group
- Can query BigQuery for analytics and monitoring
- Feature Group optimized for ML training
- No manual sync needed - fully automated
- Production-ready with proper error handling

## ✅ Phase 4: Testing & Validation - COMPLETED

**✅ Local Testing Completed:**

1. ✅ Test configuration: `python config.py` - All settings validated
2. ✅ Run setup (once): `python setup_feature_store.py` - Feature Store created
3. ✅ Test data ingestion: `python feature_pipeline.py` - Data flowing successfully
4. ✅ Verify in GCP Console:
   - BigQuery: `aqi_dataset.aqi_features` receiving hourly data
   - Vertex AI Feature Store: Feature Group auto-syncing from BigQuery

5. ✅ Query data using BigQuery SQL to verify schema and data quality

**✅ Validation Checks Passed:**
- ✅ TIMESTAMP values in correct format (ISO 8601)
- ✅ All 20+ features populated correctly
- ✅ No duplicate timestamps (duplicate prevention implemented)
- ✅ Partitioning working (data in correct day partitions)
- ✅ Schema consistency maintained across all components

**✅ Additional Validation Tools Created:**
- `scripts/verify_data.py` - Automated data verification script
- `scripts/add_day_of_week_column.py` - Schema migration script
- Comprehensive error handling and logging throughout pipeline

## ✅ Phase 5: Training Pipeline Creation - COMPLETED

**✅ IMPLEMENTED: `training_pipeline.py`:**

- ✅ Reads features from BigQuery table with proper time-based filtering
- ✅ Creates training/test splits by time (temporal validation)
- ✅ Trains multiple models (Linear Regression, Random Forest, XGBoost)
- ✅ Evaluates and saves best models with comprehensive performance metrics
- ✅ **FIXED**: Uploads models to Vertex AI Model Registry with proper directory structure
- ✅ **FIXED**: Uses built-in Vertex AI containers for model serving
- ✅ **SIMPLIFIED**: Removed custom predictor directory for cleaner architecture
- ✅ Model versioning and performance tracking implemented
- ✅ Automated model upload to Vertex AI Model Registry working

**🎯 Prerequisites Completed:**
- ✅ Data ingestion working and stable
- ✅ Feature Store populated with historical data
- ✅ Schema stable and well-defined
- ✅ CI/CD infrastructure ready for automation

**📅 Timeline:** Ready to begin once sufficient historical data is collected

## ✅ Phase 6: GitHub Actions CI/CD - COMPLETED

**✅ Created `.github/workflows/feature-pipeline.yml`:**

- ✅ Hourly schedule: `0 * * * *`
- ✅ Runs `feature_pipeline.py` with proper error handling
- ✅ Uses GitHub Secrets for secure credential management
- ✅ Manual trigger capability for testing
- ✅ Proper permissions and authentication setup

**✅ Created `.github/workflows/training-pipeline.yml`:**

- ✅ Daily schedule: `0 2 * * *`
- ✅ Runs `training_pipeline.py` (ready for Phase 5 implementation)
- ✅ Model artifact upload capabilities
- ✅ Manual trigger capability for testing

**✅ GitHub Secrets Configured:**

- ✅ `AQICN_TOKEN` - API authentication
- ✅ `GCP_PROJECT_ID` - Project identification
- ✅ `GCP_SERVICE_ACCOUNT_KEY` - JSON key for secure authentication

**✅ Additional CI/CD Features:**
- ✅ Workflow dispatch triggers for manual testing
- ✅ Proper error handling and logging
- ✅ Environment setup and dependency management

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

## ✅ Success Criteria - ALL ACHIEVED

✅ Feature Group created with 20+ features

✅ BigQuery table receives hourly data consistently

✅ Feature Group auto-syncs from BigQuery seamlessly

✅ Can query features via Feature Group SDK

✅ Pipeline runs without errors with comprehensive logging

✅ Data visible in GCP Console (BigQuery + Feature Store)

✅ Ready for GitHub Actions automation

✅ Schema management and migration capabilities

✅ Production-ready error handling and monitoring

---

## 🔧 Troubleshooting Guide

### Common Issues & Solutions

#### 1. **Schema Mismatch Errors**
**Problem:** `no such field: column_name` in BigQuery
**Solution:** Use migration scripts to add missing columns
```bash
python scripts/add_day_of_week_column.py
```

#### 2. **BigQuery Partition Errors**
**Problem:** `Cannot query over table without a filter over column(s) 'timestamp'`
**Solution:** Always use partition filters in queries
```sql
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
```

#### 3. **Authentication Issues**
**Problem:** Service account authentication failures
**Solution:** Verify credentials and project setup
```bash
gcloud auth activate-service-account --key-file="aqi-service-account.json"
gcloud config set project gen-lang-client-0939972341
```

#### 4. **Feature Store Sync Issues**
**Problem:** Feature Group not updating from BigQuery
**Solution:** Check BigQuery table schema and Feature Group configuration
- Verify entity_id and feature_timestamp columns exist
- Ensure proper data types (STRING for entity_id, TIMESTAMP for feature_timestamp)

#### 5. **GitHub Actions Workflow Issues**
**Problem:** "Run workflow" button not visible
**Solution:** Check workflow file syntax and permissions
- Ensure proper YAML indentation (2 spaces)
- Include `workflow_dispatch:` trigger
- Add permissions block

### Debugging Commands

```bash
# Test configuration
python config.py

# Verify BigQuery data
python scripts/verify_data.py

# Check Feature Store setup
python setup_feature_store.py

# Test feature pipeline
python feature_pipeline.py

# Check GitHub Actions logs
# Go to repository → Actions tab → View run logs
```

### Performance Optimization

- **BigQuery Queries:** Always use partition filters for partitioned tables
- **Feature Store:** Use entity_id for efficient lookups
- **API Calls:** Implement retry logic and rate limiting
- **Error Handling:** Log errors with context for easier debugging