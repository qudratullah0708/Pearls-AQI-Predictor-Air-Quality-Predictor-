<!-- f615abb3-a781-4c30-86e5-75bb6cbdf0cb 2927fe0f-d7b8-4e84-8a2b-3c09cf3fdd5f -->
# Custom Prediction Container for Vertex AI Model Registry

## Overview

Create a custom Docker container that loads your scikit-learn `.pkl` models and serves predictions on Vertex AI, enabling proper Model Registry integration and production-grade deployment.

## Part 1: Understanding Custom Prediction Containers

### What is a Custom Prediction Container?

A Docker container YOU create that:

1. Loads your model (any format - .pkl, .h5, .pt)
2. Defines how to make predictions
3. Runs on Vertex AI infrastructure
4. Handles HTTP requests for predictions

**Benefits:**

- ✅ Full control over prediction logic
- ✅ Works with ANY model format
- ✅ Add custom preprocessing/postprocessing
- ✅ Production-ready solution
- ✅ Portfolio-worthy MLOps skill

## Part 2: Project Structure

Create this directory structure:

```
AQI/
├── predictor/                    # New directory for custom container
│   ├── Dockerfile               # Container definition
│   ├── predictor.py             # Prediction logic
│   ├── requirements.txt         # Python dependencies
│   └── test_predictor.py        # Local testing
├── models/                      # Your trained models
│   ├── aqi_predictor_24h_random_forest.pkl
│   └── aqi_predictor_48h_random_forest.pkl
└── training_pipeline.py         # Updated to use custom container
```

## Part 3: Step-by-Step Implementation

### Step 1: Create Custom Predictor Class

**File: `predictor/predictor.py`**

This is the heart of your custom container - it defines how to load models and make predictions.

```python
"""
Custom Predictor for AQI Models
Loads scikit-learn models and serves predictions on Vertex AI
"""

import os
import joblib
import numpy as np
from google.cloud import storage
from typing import Dict, List, Any


class AQIPredictor:
    """Custom predictor for AQI forecasting models"""
    
    def __init__(self):
        """Load models from GCS or local storage"""
        print("🔧 Initializing AQI Predictor...")
        
        self.models = {}
        self.scalers = {}
        self.feature_names = [
            'hour', 'day_of_week', 'month', 'year',
            'temp', 'humidity', 'pressure', 'wind_speed', 'dew', 'pm25'
        ]
        
        # Load models
        self._load_models()
        
        print("✅ AQI Predictor initialized successfully")
    
    def _load_models(self):
        """Load all horizon models from GCS or local path"""
        model_path = os.environ.get('AIP_STORAGE_URI', '/models')
        
        horizons = ['24h', '48h', '72h']
        
        for horizon in horizons:
            try:
                # Try to load model
                model_file = f"{model_path}/model_{horizon}.pkl"
                
                if model_file.startswith('gs://'):
                    # Load from GCS
                    self.models[horizon] = self._load_from_gcs(model_file)
                else:
                    # Load from local path
                    if os.path.exists(model_file):
                        self.models[horizon] = joblib.load(model_file)
                        print(f"✅ Loaded {horizon} model")
                    else:
                        print(f"⚠️  Model not found: {model_file}")
            
            except Exception as e:
                print(f"❌ Error loading {horizon} model: {e}")
    
    def _load_from_gcs(self, gcs_path: str):
        """Load model from Google Cloud Storage"""
        storage_client = storage.Client()
        
        # Parse GCS path
        path_parts = gcs_path.replace('gs://', '').split('/')
        bucket_name = path_parts[0]
        blob_name = '/'.join(path_parts[1:])
        
        # Download model
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        # Load into memory
        model_bytes = blob.download_as_bytes()
        model = joblib.loads(model_bytes)
        
        return model
    
    def predict(self, instances: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Make predictions for given instances
        
        Args:
            instances: List of dicts with feature values
            
        Returns:
            Dict with predictions for each horizon
        """
        try:
            predictions = {}
            
            # Convert instances to numpy array
            X = self._preprocess_instances(instances)
            
            # Make predictions for each horizon
            for horizon, model in self.models.items():
                if model is not None:
                    preds = model.predict(X)
                    predictions[horizon] = {
                        'aqi_values': preds.tolist(),
                        'horizon': horizon
                    }
            
            return {'predictions': predictions}
        
        except Exception as e:
            return {'error': str(e)}
    
    def _preprocess_instances(self, instances: List[Dict]) -> np.ndarray:
        """Convert instances to numpy array in correct order"""
        X = []
        
        for instance in instances:
            # Extract features in correct order
            features = [
                instance.get(feat, 0) for feat in self.feature_names
            ]
            X.append(features)
        
        return np.array(X)
    
    def health_check(self) -> Dict[str, str]:
        """Health check endpoint"""
        return {
            'status': 'healthy',
            'models_loaded': list(self.models.keys()),
            'features_expected': self.feature_names
        }
```

**Key Learning Points:**

- `__init__`: Loads models when container starts
- `predict`: Main prediction logic
- `health_check`: Vertex AI uses this to verify container is ready
- `_load_from_gcs`: Loads models from Cloud Storage

### Step 2: Create Flask/FastAPI Wrapper

**File: `predictor/app.py`**

Wraps your predictor in a web server that Vertex AI can call:

```python
"""
Flask app wrapper for custom predictor
Vertex AI calls this via HTTP
"""

from flask import Flask, request, jsonify
from predictor import AQIPredictor
import os

app = Flask(__name__)

# Initialize predictor on startup
predictor = AQIPredictor()

@app.route('/predict', methods=['POST'])
def predict():
    """
    Prediction endpoint
    Vertex AI calls this with JSON payload
    """
    try:
        # Get instances from request
        content = request.json
        instances = content.get('instances', [])
        
        # Make predictions
        predictions = predictor.predict(instances)
        
        return jsonify(predictions)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify(predictor.health_check())

if __name__ == '__main__':
    # Vertex AI sets AIP_HTTP_PORT
    port = int(os.environ.get('AIP_HTTP_PORT', 8080))
    app.run(host='0.0.0.0', port=port)
```

### Step 3: Create Dockerfile

**File: `predictor/Dockerfile`**

Defines how to build your container:

```dockerfile
# Use Python base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy predictor code
COPY predictor.py .
COPY app.py .

# Expose port
EXPOSE 8080

# Set environment variables
ENV AIP_HTTP_PORT=8080
ENV PYTHONUNBUFFERED=1

# Run the app
CMD ["python", "app.py"]
```

**Learning: Docker Layers**

- Each `RUN`/`COPY` creates a layer
- Order matters for caching
- Requirements installed first (changes less often)

### Step 4: Create Requirements File

**File: `predictor/requirements.txt`**

```
flask==3.0.0
gunicorn==21.2.0
scikit-learn==1.3.0
xgboost==2.0.0
joblib==1.3.2
numpy==1.24.3
google-cloud-storage==2.10.0
```

### Step 5: Build and Test Locally

**Test your container locally before deploying:**

```bash
# Navigate to predictor directory
cd predictor

# Build Docker image
docker build -t aqi-predictor-fastapi:latest .

# Run container locally
cd predictor && docker run --rm -p 8080:8080 -v "$(pwd)/../models:/models" aqi-predictor-fastapi:latest

# Test with curl (in another terminal)
curl -X POST http://localhost:8080/predict \
  -H "Content-Type: application/json" \
  -d '{
    "instances": [{
      "hour": 14,
      "day_of_week": 2,
      "month": 10,
      "year": 2025,
      "temp": 25.5,
      "humidity": 65.0,
      "pressure": 1013.0,
      "wind_speed": 5.5,
      "dew": 18.0,
      "pm25": 85.0
    }]
  }'
```

### Step 6: Push to Google Container Registry

```bash
# Authenticate Docker with GCR
gcloud auth configure-docker

# Tag image for GCR
docker tag aqi-predictor:latest \
  gcr.io/gen-lang-client-0939972341/aqi-predictor:v1

# Push to GCR
docker push gcr.io/gen-lang-client-0939972341/aqi-predictor:v1
```

### Step 7: Upload Models to GCS with Container

**Update `training_pipeline.py`:**

```python
def upload_to_model_registry_custom(saved_models, results_df):
    """Upload models using custom prediction container"""
    
    for saved_model in saved_models:
        horizon = saved_model['horizon']
        model_name = saved_model['model_name']
        model_path = saved_model['filename']
        
        # 1. Upload model to GCS
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        gcs_model_dir = f"{GCS_MODEL_PATH}/{horizon}/{model_name}_v{timestamp}"
        
        # Upload model file
        storage_client = storage.Client(project=GCP_PROJECT_ID)
        bucket = storage_client.bucket(MODEL_ARTIFACTS_BUCKET)
        
        blob = bucket.blob(f"{gcs_model_dir}/model_{horizon}.pkl")
        blob.upload_from_filename(model_path)
        
        gcs_uri = f"gs://{MODEL_ARTIFACTS_BUCKET}/{gcs_model_dir}"
        
        # 2. Register in Model Registry with custom container
        model = aiplatform.Model.upload(
            display_name=f"aqi-predictor-{horizon}-{model_name}",
            artifact_uri=gcs_uri,
            serving_container_image_uri=f"gcr.io/{GCP_PROJECT_ID}/aqi-predictor:v1",
            serving_container_predict_route="/predict",
            serving_container_health_route="/health",
            serving_container_ports=[8080]
        )
        
        print(f"✅ {horizon} model uploaded with custom container!")
```

## Part 4: Testing & Validation

### Test 1: Local Docker Test

```bash
# Should return predictions
curl localhost:8080/predict -d '{"instances": [...]}'
```

### Test 2: Health Check

```bash
# Should return "healthy"
curl localhost:8080/health
```

### Test 3: Model Registry

1. Run updated training_pipeline.py
2. Check Vertex AI Model Registry
3. Verify models appear

## Part 5: Deploy to Vertex AI Endpoint (Optional)

Once models are in registry, deploy to endpoint:

```python
endpoint = aiplatform.Endpoint.create(display_name="aqi-endpoint")

model.deploy(
    endpoint=endpoint,
    machine_type="n1-standard-2",
    min_replica_count=1,
    max_replica_count=3
)

# Make predictions
predictions = endpoint.predict(instances=[...])
```

## Success Criteria

### Must Have:

- ✅ Custom predictor loads models correctly
- ✅ Docker container builds successfully
- ✅ Local testing passes
- ✅ Models upload to Model Registry
- ✅ Models appear in GCP Console

### Nice to Have:

- ✅ Deployed to Vertex AI Endpoint
- ✅ Can make predictions via API
- ✅ Monitoring and logging set up

## Timeline

**Day 1 (4-5 hours):**

- Create predictor.py and app.py
- Create Dockerfile
- Test locally with Docker

**Day 2 (3-4 hours):**

- Push to Container Registry
- Update training_pipeline.py
- Test Model Registry upload

**Day 3 (2-3 hours):**

- Deploy to Vertex AI Endpoint
- Test end-to-end
- Document for internship

## Learning Resources

**Docker Basics:**

- Official Docker tutorial
- Understanding layers and caching
- Multi-stage builds

**Vertex AI Custom Containers:**

- Google Cloud documentation
- Custom prediction routines
- Container requirements

## For Your Internship Demo

**Perfect story:**

> "I implemented a custom prediction container using Docker to deploy scikit-learn models to Vertex AI Model Registry. This demonstrates:

> - Docker containerization skills

> - Production MLOps practices

> - Full control over prediction pipeline

> - Scalable deployment on Google Cloud

>

> The container loads joblib-saved models, handles preprocessing, and serves predictions via Flask API on Vertex AI infrastructure."

## Next Steps

1. Create `predictor/` directory
2. Implement `predictor.py` with AQIPredictor class
3. Create `app.py` Flask wrapper
4. Build and test Docker container locally
5. Push to Google Container Registry
6. Update training_pipeline.py
7. Test Model Registry upload

### To-dos

- [ ] Create api/app.py with FastAPI server and prediction endpoints
- [ ] Implement model loading and prediction logic in backend
- [ ] Test API endpoints with Postman or curl
- [ ] Create React frontend with Vite/CRA
- [ ] Build PredictionForm component with weather inputs
- [ ] Build PredictionResults component with AQI visualization
- [ ] Implement API service layer and connect to backend
- [ ] Add HistoricalChart component with Recharts
- [ ] Add ModelPerformance component showing MAE, R², etc
- [ ] Deploy backend to Cloud Run and frontend to Vercel