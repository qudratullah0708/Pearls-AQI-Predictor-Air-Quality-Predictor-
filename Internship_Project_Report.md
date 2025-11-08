# 🌍 AQI Forecasting System - Internship Project Report

**Student:** Qudrat Ullah | **Institution:** 10Pearls Internship | **Date:** November 2025

---

## 📋 Executive Summary

**Project Goal:** Build an end-to-end MLOps pipeline for Air Quality Index (AQI) forecasting that predicts AQI levels 24, 48, and 72 hours ahead for Islamabad, Pakistan.

**Key Achievements:**
- ✅ Zero-cost MLOps system (migrated from cloud, saving $100s/month)
- ✅ Production-ready pipelines with automated data collection and model training
- ✅ Multi-horizon predictions (24h, 48h, 72h) with 3 ML models
- ✅ Complete system: data collection → feature store → models → web dashboard

**Final Results:**
| Horizon | Best Model | MAE | RMSE | Status |
|---------|-----------|-----|------|--------|
| 24h | XGBoost | 14.58 | 20.82 | ✅ Best |
| 48h | XGBoost | 16.59 | 22.63 | ✅ Best |
| 72h | Random Forest | 17.51 | 20.40 | ✅ Best |

---

## 📊 1. Data Collection

### 1.1 Data Source & Features
- **API:** AQICN.org (free public API, hourly updates)
- **Location:** Islamabad, Pakistan (US Embassy monitoring station)
- **Features Collected:** 21 features
  - **Air Quality:** AQI, PM2.5, dominant pollutant
  - **Weather:** Temperature, humidity, pressure, wind speed, dew point
  - **Time Features:** Hour, day, month, year, day of week
  - **Derived Features:** AQI change, rolling averages

### 1.2 Data Pipeline Architecture
```
AQICN API → Feature Pipeline → Feast Feature Store → Training Pipeline → Models
```

**Implementation:**
1. **API Integration** (`feature_pipeline.py`): Fetches real-time AQI data hourly, extracts 21 features, validates data quality
2. **Feature Engineering**: Time-based features (hour, day_of_week), derived features (AQI change, rolling stats), normalization
3. **Storage** (Feast Feature Store):
   - **Offline Store:** Parquet files (historical data for training)
   - **Online Store:** SQLite database (real-time feature serving)
   - **Entity:** location_id (islamabad_us_embassy)
   - **Feature View:** 21 features with proper data types

### 1.3 Data Statistics
- **Historical Data:** 139+ records (October 2025)
- **Data Range:** 2025-10-09 to 2025-10-18
- **Collection Method:** Automated via GitHub Actions (hourly)
- **Data Quality:** Validated for completeness and consistency

---

## 🔬 2. Approaches Tried

### 2.1 Approach 1: Cloud-Based (BigQuery + Vertex AI)
**Architecture:** `AQICN API → GitHub Actions → BigQuery → Vertex AI Feature Store → Vertex AI Models`

**Why:** Industry-standard cloud MLOps stack, scalable, production-ready

**Challenges:**
- ❌ High costs: $100-300/month in GCP credits
- ❌ Complex setup: Service account authentication, IAM permissions
- ❌ Network latency: Slow development (10+ seconds per query)
- ❌ Dependencies: Required GCP project setup

**Result:** Functional but expensive and complex for internship project.

### 2.2 Approach 2: Local Feature Store (Feast) - **FINAL SOLUTION**
**Architecture:** `AQICN API → GitHub Actions → Parquet Files → Feast Feature Store → Local Models`

**Why:**
- ✅ Zero cost (no cloud dependencies)
- ✅ Fast development (local file access, < 2 seconds)
- ✅ Simple setup (no authentication required)
- ✅ Industry standard (Feast used by Uber, Gojek)
- ✅ Educational (learn feature stores without cloud complexity)

**Migration Process:**
1. Converted BigQuery schema to Feast feature definitions
2. Migrated 139 historical records from CSV to Parquet
3. Updated data pipelines to use Feast SDK
4. Fixed timezone handling and data type issues
5. Validated model performance (maintained or improved)

**Result:** ✅ Successful migration with improved performance and zero costs.

### 2.3 Model Selection Approaches

**Models Evaluated:**
1. **Linear Regression** (Baseline)
   - Simple, interpretable, fast training
   - Lower accuracy for non-linear patterns

2. **Random Forest** (Ensemble)
   - Handles non-linear relationships
   - Feature importance insights
   - Best for 72h predictions

3. **XGBoost** (Gradient Boosting)
   - Best performance for 24h and 48h
   - Handles complex patterns
   - Slightly longer training time

**Selection Criteria:** Lowest MAE, stability, interpretability, training time

**Final Selection:**
- **24h & 48h:** XGBoost (best accuracy)
- **72h:** Random Forest (best stability)

### 2.4 Feature Engineering Approaches

**Approach 1: Basic Features Only**
- Raw API data: AQI, PM2.5, weather variables
- **Result:** Limited predictive power

**Approach 2: Time Features Added**
- Hour, day_of_week, month, year
- **Result:** Significant improvement (captures daily/weekly patterns)

**Approach 3: Derived Features**
- AQI change, rolling averages
- **Result:** Marginal improvement (requires more historical data)

**Final Feature Set:** 10 features used for training
- Time: hour, day_of_week, month, year
- Weather: temp, humidity, pressure, wind_speed, dew
- Air Quality: pm25

---

## 🎯 3. Final Solution

### 3.1 System Architecture
```
┌─────────────┐
│  AQICN API  │ (Hourly Data)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Feature Pipe │ (Data Collection & Engineering)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Feast Store  │ (Parquet + SQLite)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Train Pipe   │ (Model Training - Daily)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Models    │ (XGBoost, Random Forest)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  FastAPI    │ (Backend API)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ React App   │ (Frontend Dashboard)
└─────────────┘
```

### 3.2 Key Components

**1. Data Pipeline** (`feature_pipeline.py`)
- Fetches data from AQICN API hourly
- Engineers 21 features
- Stores in Feast Feature Store
- Automated via GitHub Actions

**2. Training Pipeline** (`training_pipeline.py`)
- Loads historical data from Feast
- Creates multi-horizon targets (24h, 48h, 72h)
- Trains 3 model types per horizon (Linear Regression, Random Forest, XGBoost)
- Evaluates and selects best models
- Saves models with versioning
- Automated daily via GitHub Actions

**3. Feature Store** (Feast)
- **Offline Store:** Parquet files for training
- **Online Store:** SQLite for real-time serving
- **Feature Views:** 21 features defined
- **Materialization:** Automated sync from offline to online

**4. Backend API** (`backend/api.py`)
- FastAPI REST API
- Endpoints: `/current-aqi`, `/predict/{horizon}`, `/predictions/all`
- Model serving with performance tracking
- Real-time feature retrieval from Feast

**5. Frontend Dashboard** (`frontend/aqi-predictor/`)
- React application
- Real-time AQI display
- 3-day forecast visualization
- Model performance monitoring
- Responsive design

### 3.3 Automation & CI/CD
- **Feature Pipeline:** Runs hourly (data collection)
- **Training Pipeline:** Runs daily (model retraining)
- **Data Sync:** Automated synchronization of artifacts
- **Error Handling:** Comprehensive logging and notifications

### 3.4 Model Deployment Strategy
- Models versioned with timestamps
- New models deployed only if RMSE improves
- Previous models kept as fallback
- Deployment metadata tracked in JSON

---

## 📈 4. Results & Achievements

### 4.1 Model Performance
**Best Models Selected:**
- **24h:** XGBoost (MAE: 14.58, RMSE: 20.82)
- **48h:** XGBoost (MAE: 16.59, RMSE: 22.63)
- **72h:** Random Forest (MAE: 17.51, RMSE: 20.40)

**Key Insights:**
- **Temperature** is the most important feature across all horizons
- **Time features** (hour, day_of_week) provide strong predictive power
- **Weather variables** (dew, pressure, humidity) enhance accuracy
- **Performance improved** after migration to Feast feature store

### 4.2 Migration Success
**Before (Cloud):**
- Cost: $100-300/month | Setup: 30+ minutes | Data loading: ~10 seconds

**After (Local):**
- Cost: $0/month | Setup: 5 minutes | Data loading: ~2 seconds

**Impact:** ✅ 100% cost reduction | ✅ 5x faster development | ✅ Simplified setup | ✅ Maintained functionality

### 4.3 Technical Achievements
1. **Feature Store Implementation:** Successfully implemented Feast Feature Store, migrated 139 historical records, maintained data integrity
2. **MLOps Pipeline:** Automated data collection (hourly), automated model training (daily), model versioning and deployment, performance tracking
3. **System Integration:** End-to-end pipeline from API to dashboard, real-time predictions via REST API, interactive web dashboard

### 4.4 Learning Outcomes
**Technical Skills:** Feature store implementation (Feast), time-series forecasting, MLOps pipeline development, system migration and optimization, API development (FastAPI), frontend development (React)

**Best Practices:** Automated testing and validation, model versioning and deployment, performance monitoring, cost optimization, documentation and code quality

---

## 🎓 5. Key Learnings & Challenges

### 5.1 Challenges Overcome
1. **Timezone Handling:** Mixed timezone-aware/naive timestamps → Comprehensive timezone normalization to UTC
2. **Data Type Management:** Parquet strict type requirements → Explicit type conversion and validation
3. **Cloud Migration:** High costs and complex setup → Local Feast feature store implementation
4. **Model Selection:** Choosing between multiple models → Systematic evaluation with multiple metrics

### 5.2 Best Practices Applied
- Incremental development (start with baseline, add features gradually)
- Automation (CI/CD pipelines, automated model training)
- Documentation (comprehensive README, code comments)
- Testing & Validation (data quality checks, model performance validation)

---

## 🚀 6. Future Improvements

### Short-term
- Add more historical data for better accuracy
- Implement advanced feature engineering (lag features, rolling statistics)
- Add model explainability (SHAP values)
- Enhance error handling and monitoring

### Long-term
- Expand to multiple cities
- Implement real-time alerts for hazardous AQI levels
- Add mobile app for notifications
- Integrate with weather APIs for better predictions

---

## 📝 Conclusion

This project successfully demonstrates an end-to-end MLOps pipeline for AQI forecasting, from data collection to web dashboard. The migration from cloud to local infrastructure resulted in **zero operational costs** while maintaining full functionality and improving development speed.

**Key Takeaways:**
- ✅ Production-ready MLOps system
- ✅ Zero-cost operation
- ✅ Industry-standard tools (Feast, XGBoost)
- ✅ Comprehensive automation
- ✅ Real-world application

**Skills Demonstrated:**
- Data engineering and feature store implementation
- Machine learning model development and evaluation
- System architecture and migration
- API development and frontend integration
- Automation and CI/CD

---

**Report Generated:** November 2025 | **Project Repository:** [GitHub Link] | **Contact:** [Your Email]

---

*This report summarizes the AQI Forecasting System internship project, covering data collection, approaches tried, final solution, and key achievements in a concise format suitable for a 7-minute presentation.*
