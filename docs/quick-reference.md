# 🚀 AQI Project - Quick Reference Guide

## 📋 Common Commands

### Data Operations
```bash
# Convert CSV to Parquet (with merge capability)
python scripts/convert_csv_to_parquet.py

# Sync data from GitHub Actions
python sync_feast_data.py --daily
python sync_feast_data.py --latest
python sync_feast_data.py --weekly

# Verify data integrity
python scripts/verify_data.py

# Test Feast feature store
python scripts/test_feast.py
```

### Feature Store Operations
```bash
# Initialize Feast repository
cd feature_repo
feast apply
feast materialize 2025-10-09 2025-10-18
cd ..

# Check feature store status
cd feature_repo
feast registry list-feature-views
feast registry list-entities
cd ..
```

### Model Operations
```bash
# Run feature pipeline (collect new data)
python feature_pipeline.py

# Train models
python training_pipeline.py

# Check model performance
cat model_performance_history.csv
```

## 🔧 Troubleshooting

### Common Issues

#### Sync Script Fails
```bash
# Check GitHub CLI installation
gh --version

# Authenticate with GitHub
gh auth login

# Check workflow runs
gh run list --workflow=feature-pipeline.yml
```

#### Feast Materialization Errors
```bash
# Check Feast installation
pip show feast

# Verify feature store configuration
cd feature_repo
feast config
cd ..

# Test with sample data
python scripts/test_feast.py
```

#### Data Validation Issues
```bash
# Check parquet file integrity
python -c "import pandas as pd; df = pd.read_parquet('feature_repo/data/aqi_features.parquet'); print(f'Records: {len(df)}, Date range: {df[\"timestamp\"].min()} to {df[\"timestamp\"].max()}')"

# Verify data freshness
python scripts/verify_data.py
```

## 📊 Data Status Checks

### Check Current Data
```python
import pandas as pd

# Load current data
df = pd.read_parquet('feature_repo/data/aqi_features.parquet')

print(f"Total records: {len(df)}")
print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
print(f"Latest AQI: {df['aqi'].iloc[-1]}")
print(f"Columns: {df.columns.tolist()}")
```

### Check Online Store
```python
from feast_utils import get_latest_features

# Get latest features from online store
features = get_latest_features()
print(f"Latest AQI: {features['aqi']}")
print(f"Latest PM2.5: {features['pm25']}")
```

## 🔄 Sync Strategies

### Daily Sync (Recommended)
```bash
python sync_feast_data.py --daily
```
- Syncs latest run from last 24 hours
- Best for active development
- Ensures fresh data

### Weekly Sync
```bash
python sync_feast_data.py --weekly
```
- Syncs latest run from last 7 days
- Good for learning/testing phases
- Lower maintenance

### On-Demand Sync
```bash
python sync_feast_data.py --latest
```
- Syncs most recent completed run
- Use when you need fresh data immediately
- Manual operation

## 📁 File Locations

### Core Files
- `feature_pipeline.py` - Data collection pipeline
- `training_pipeline.py` - Model training pipeline
- `sync_feast_data.py` - GitHub Actions sync
- `feast_utils.py` - Feast helper functions
- `config.py` - Configuration settings

### Data Files
- `feature_repo/data/aqi_features.parquet` - Historical features
- `feature_repo/data/online_store.db` - Real-time features
- `feature_repo/data/registry.db` - Feature metadata
- `model_performance_history.csv` - Performance tracking

### Scripts
- `scripts/convert_csv_to_parquet.py` - CSV conversion
- `scripts/setup_feature_store.py` - Feast setup
- `scripts/verify_data.py` - Data validation
- `scripts/test_feast.py` - Feature store testing

## 🎯 Performance Monitoring

### Model Performance
```bash
# View latest performance metrics
tail -5 model_performance_history.csv

# Check specific model performance
grep "24h" model_performance_history.csv | tail -1
```

### Data Freshness
```bash
# Check data age
python -c "
import pandas as pd
from datetime import datetime, timezone
df = pd.read_parquet('feature_repo/data/aqi_features.parquet')
latest = df['timestamp'].max()
now = pd.Timestamp.now(timezone.utc)
hours_old = (now - latest).total_seconds() / 3600
print(f'Data is {hours_old:.1f} hours old')
"
```

## 🚨 Error Recovery

### Reset Feature Store
```bash
# Backup current data
cp feature_repo/data/aqi_features.parquet feature_repo/data/aqi_features_backup.parquet

# Reinitialize Feast
cd feature_repo
feast apply
feast materialize 2025-10-09 2025-10-21
cd ..
```

### Recover from Sync Issues
```bash
# Clean temp files
rm -rf temp_artifacts

# Re-run sync
python sync_feast_data.py --daily
```

## 📞 Support

### Documentation
- `docs/project-overview.md` - Complete project overview
- `docs/migration_report.md` - Migration journey
- `docs/approach.md` - Technical approach
- `Readme.md` - Main project documentation

### Key Learning Resources
- Feast Documentation: https://docs.feast.dev/
- MLOps Best Practices: Industry standards
- Time Series Forecasting: Scikit-learn guides

---

*Quick reference for AQI Forecasting System - Keep this handy for daily operations!*
