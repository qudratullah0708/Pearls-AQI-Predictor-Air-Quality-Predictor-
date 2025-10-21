#!/bin/bash
# daily_sync.sh - Automated daily sync script
# Add this to your daily routine or cron job

echo "🕐 Starting daily Feast data sync..."
echo "Date: $(date)"

# Change to your project directory
cd /path/to/your/AQI  # Update this path

# Run the sync script
python sync_feast_data.py --daily

# Check if sync was successful
if [ $? -eq 0 ]; then
    echo "✅ Daily sync completed successfully"
    
    # Optional: Run training pipeline if you have enough data
    echo "🤖 Checking if we should run training..."
    python -c "
import pandas as pd
df = pd.read_parquet('feature_repo/data/aqi_features.parquet')
hours = (pd.Timestamp.now() - pd.to_datetime(df['timestamp'].max())).total_seconds() / 3600
if len(df) >= 72 and hours < 2:
    print('✅ Data is fresh and sufficient - running training pipeline')
    import subprocess
    subprocess.run(['python', 'training_pipeline.py'])
else:
    print(f'⏳ Not enough data yet: {len(df)} records, {hours:.1f} hours old')
"
else
    echo "❌ Daily sync failed"
    exit 1
fi

echo "🎉 Daily sync routine completed"
