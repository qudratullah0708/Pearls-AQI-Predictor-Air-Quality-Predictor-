from feast import Entity, FeatureView, Field, FileSource
from feast.types import Float32, Int32, String
from feast.value_type import ValueType
from datetime import timedelta

# Step 1: Define the Entity (represents Islamabad monitoring station)
aqi_location = Entity(
    name="aqi_location",
    join_keys=["location_id"],
    value_type=ValueType.STRING,
    description="AQI monitoring location (Islamabad US Embassy)"
)

# Step 2: Define the Data Source (where features are stored)
aqi_source = FileSource(
    path='data/aqi_features.parquet',
    timestamp_field='timestamp'
)

# Step 3: Define the Feature View (schema of all features)
aqi_feature_view = FeatureView(
    name='aqi_features',
    entities=[aqi_location],
    ttl=timedelta(days=365),  # Features valid for 1 year
    schema=[
        # Location info
        Field(name="city", dtype=String),
        Field(name="latitude", dtype=Float32),
        Field(name="longitude", dtype=Float32),
        
        # Air quality measurements
        Field(name="aqi", dtype=Int32),
        Field(name="dominant_pollutant", dtype=String),
        Field(name="pm25", dtype=Float32),
        
        # Weather features
        Field(name="dew", dtype=Float32),
        Field(name="humidity", dtype=Float32),
        Field(name="pressure", dtype=Float32),
        Field(name="temp", dtype=Float32),
        Field(name="wind_speed", dtype=Float32),
        
        # Time features
        Field(name="hour", dtype=Int32),
        Field(name="day", dtype=Int32),
        Field(name="month", dtype=Int32),
        Field(name="year", dtype=Int32),
        Field(name="day_of_week", dtype=Int32),
        
        # Derived features
        Field(name="aqi_change", dtype=Float32),
        Field(name="aqi_roll3", dtype=Float32),
        
        # Feature store metadata (keep these from your CSV)
        Field(name="entity_id", dtype=String),
        Field(name="feature_timestamp", dtype=String),
    ],
    source=aqi_source,
    online=True,  # Enable online serving
)