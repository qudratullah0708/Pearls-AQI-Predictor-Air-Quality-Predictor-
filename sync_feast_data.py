#!/usr/bin/env python3
"""
Sync Feast data from GitHub Actions artifacts to local machine
Usage: 
  python sync_feast_data.py [run_number]           # Sync specific run
  python sync_feast_data.py --latest              # Sync latest run
  python sync_feast_data.py --daily               # Sync latest run from today
  python sync_feast_data.py --weekly              # Sync latest run from this week
"""

import os
import sys
import subprocess
import zipfile
import shutil
import argparse
from pathlib import Path
from datetime import datetime, timedelta

def get_workflow_runs(days_back=1):
    """Get workflow runs from the last N days"""
    try:
        result = subprocess.run([
            "gh", "run", "list", "--workflow=feature-pipeline.yml", 
            f"--limit=100", "--json", "number,status,createdAt"
        ], capture_output=True, text=True, check=True)
        
        import json
        runs = json.loads(result.stdout)
        
        # Filter by date if specified
        if days_back:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            filtered_runs = []
            for run in runs:
                run_date = datetime.fromisoformat(run["createdAt"].replace("Z", "+00:00"))
                if run_date >= cutoff_date:
                    filtered_runs.append(run)
            return filtered_runs
        
        return runs
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error getting workflow runs: {e}")
        return []

def download_artifact(run_number=None, days_back=None):
    """Download the latest Feast artifact from GitHub Actions"""
    print("🔄 Downloading Feast data from GitHub Actions...")
    
    try:
        # Get runs based on criteria
        if days_back:
            runs = get_workflow_runs(days_back)
            if not runs:
                print(f"❌ No workflow runs found in the last {days_back} days")
                return False
            
            # Find the latest completed run
            completed_runs = [r for r in runs if r["status"] == "completed"]
            if not completed_runs:
                print(f"❌ No completed runs found in the last {days_back} days")
                return False
            
            run_number = completed_runs[0]["number"]
            print(f"✅ Found latest run from last {days_back} days: {run_number}")
            
        elif run_number is None:
            print("📋 Getting latest workflow run...")
            runs = get_workflow_runs(1)  # Last 24 hours
            if not runs:
                print("❌ No workflow runs found")
                return False
                
            run_number = runs[0]["number"]
            status = runs[0]["status"]
            
            if status != "completed":
                print(f"⚠️  Latest run {run_number} status: {status}")
                return False
                
            print(f"✅ Found latest run: {run_number}")
        
        # Download the artifact
        artifact_name = f"feast-offline-store-{run_number}"
        print(f"📥 Downloading artifact: {artifact_name}")
        
        subprocess.run([
            "gh", "run", "download", str(run_number), 
            "-n", artifact_name, "-D", "temp_artifacts"
        ], check=True)
        
        print("✅ Artifact downloaded successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error downloading artifact: {e}")
        return False
    except FileNotFoundError:
        print("❌ GitHub CLI (gh) not found. Install it first:")
        print("   https://cli.github.com/")
        return False

def extract_and_sync():
    """Extract artifact and sync to local Feast store"""
    print("📦 Extracting and syncing data...")
    
    try:
        # Find the downloaded zip file
        temp_dir = Path("temp_artifacts")
        if not temp_dir.exists():
            print("❌ No temp_artifacts directory found")
            return False
            
        zip_files = list(temp_dir.glob("*.zip"))
        if not zip_files:
            print("❌ No zip file found in temp_artifacts")
            return False
            
        zip_file = zip_files[0]
        print(f"📂 Found zip file: {zip_file}")
        
        # Extract the zip
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Copy files to local Feast store
        feast_data_dir = Path("feature_repo/data")
        feast_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy parquet file
        parquet_src = temp_dir / "feature_repo" / "data" / "aqi_features.parquet"
        parquet_dst = feast_data_dir / "aqi_features.parquet"
        
        if parquet_src.exists():
            shutil.copy2(parquet_src, parquet_dst)
            print(f"✅ Synced: {parquet_dst}")
        else:
            print("⚠️  No parquet file found in artifact")
        
        # Copy registry file
        registry_src = temp_dir / "feature_repo" / "data" / "registry.db"
        registry_dst = feast_data_dir / "registry.db"
        
        if registry_src.exists():
            shutil.copy2(registry_src, registry_dst)
            print(f"✅ Synced: {registry_dst}")
        else:
            print("⚠️  No registry file found in artifact")
        
        # Clean up
        shutil.rmtree(temp_dir)
        print("🧹 Cleaned up temporary files")
        
        return True
        
    except Exception as e:
        print(f"❌ Error extracting/syncing: {e}")
        return False

def verify_sync():
    """Verify the sync worked by checking data"""
    print("🔍 Verifying sync...")
    
    try:
        import pandas as pd
        parquet_file = Path("feature_repo/data/aqi_features.parquet")
        
        if not parquet_file.exists():
            print("❌ No parquet file found after sync")
            return False
            
        df = pd.read_parquet(parquet_file)
        print(f"✅ Data verification successful:")
        print(f"   📊 Total records: {len(df)}")
        print(f"   📅 Latest timestamp: {df['timestamp'].max()}")
        print(f"   📅 Earliest timestamp: {df['timestamp'].min()}")
        
        # Calculate data freshness
        latest_time = pd.to_datetime(df['timestamp'].max())
        now = pd.Timestamp.now()
        hours_old = (now - latest_time).total_seconds() / 3600
        
        print(f"   ⏰ Data freshness: {hours_old:.1f} hours old")
        
        if hours_old > 25:
            print("   ⚠️  Data is more than 24 hours old - consider syncing more frequently")
        elif hours_old > 2:
            print("   ✅ Data is reasonably fresh")
        else:
            print("   🎉 Data is very fresh!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying data: {e}")
        return False

def show_sync_strategies():
    """Show different sync strategies and their trade-offs"""
    print("\n📚 Sync Strategies Guide:")
    print("=" * 50)
    print("🕐 DAILY SYNC (Recommended):")
    print("   • Run: python sync_feast_data.py --daily")
    print("   • Data loss: Max 24 hours")
    print("   • Best for: Regular development work")
    print("   • Maintenance: Low")
    
    print("\n📅 WEEKLY SYNC:")
    print("   • Run: python sync_feast_data.py --weekly")
    print("   • Data loss: Max 7 days")
    print("   • Best for: Learning/testing phases")
    print("   • Maintenance: Very low")
    
    print("\n🎯 ON-DEMAND SYNC:")
    print("   • Run: python sync_feast_data.py --latest")
    print("   • Data loss: Depends on when you sync")
    print("   • Best for: When you need fresh data")
    print("   • Maintenance: Manual")
    
    print("\n📊 GITHUB ACTIONS ARTIFACTS:")
    print("   • Retention: 30 days (configurable)")
    print("   • Storage: 10GB per repository")
    print("   • Frequency: Every hour (your pipeline)")
    print("   • Access: Via GitHub CLI or web interface")

def main():
    """Main sync function"""
    parser = argparse.ArgumentParser(description="Sync Feast data from GitHub Actions")
    parser.add_argument("run_number", nargs="?", help="Specific run number to sync")
    parser.add_argument("--latest", action="store_true", help="Sync latest run")
    parser.add_argument("--daily", action="store_true", help="Sync latest run from today")
    parser.add_argument("--weekly", action="store_true", help="Sync latest run from this week")
    parser.add_argument("--help-strategies", action="store_true", help="Show sync strategies")
    
    args = parser.parse_args()
    
    if args.help_strategies:
        show_sync_strategies()
        return
    
    print("🚀 Starting Feast data sync from GitHub Actions")
    print("=" * 50)
    
    # Check if gh CLI is available
    try:
        subprocess.run(["gh", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ GitHub CLI (gh) not found!")
        print("📥 Install it from: https://cli.github.com/")
        print("🔑 Then authenticate: gh auth login")
        return
    
    # Determine sync strategy
    run_number = args.run_number
    days_back = None
    
    if args.daily:
        days_back = 1
        print("📅 Using DAILY sync strategy")
    elif args.weekly:
        days_back = 7
        print("📅 Using WEEKLY sync strategy")
    elif args.latest:
        print("🎯 Using LATEST sync strategy")
    elif run_number:
        print(f"🎯 Syncing specific run: {run_number}")
    
    # Download artifact
    if not download_artifact(run_number, days_back):
        return
    
    # Extract and sync
    if not extract_and_sync():
        return
    
    # Verify
    if not verify_sync():
        return
    
    print("\n🎉 Sync completed successfully!")
    print("✅ Your local Feast data is now up to date with GitHub Actions")
    
    # Show next steps
    print("\n💡 Next steps:")
    print("   • Run your training pipeline: python training_pipeline.py")
    print("   • Check model performance: cat model_performance_history.csv")
    print("   • Set up daily sync: Add to your daily routine")

if __name__ == "__main__":
    main()
