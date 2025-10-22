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
from feast_utils import materialize_to_online_store

def get_workflow_runs(days_back=1):
    """Get workflow runs from the last N days"""
    try:
        # Use full path to gh.exe on Windows
        import platform
        if platform.system() == "Windows":
            gh_cmd = r"C:\Program Files\GitHub CLI\gh.exe"
        else:
            gh_cmd = "gh"
            
        result = subprocess.run([
            gh_cmd, "run", "list", "--workflow=feature-pipeline.yml", 
            f"--limit=100", "--json", "number,status,createdAt,databaseId"
        ], capture_output=True, text=True, check=True)
        
        import json
        runs = json.loads(result.stdout)
        
        # Filter by date if specified
        if days_back:
            # Create timezone-aware cutoff_date in UTC to match GitHub API response
            from datetime import timezone
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
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
            
            run_number = completed_runs[0]["databaseId"]  # Use databaseId instead of number
            print(f"✅ Found latest run from last {days_back} days: {run_number}")
            
        elif run_number is None:
            print("📋 Getting latest workflow run...")
            runs = get_workflow_runs(1)  # Last 24 hours
            if not runs:
                print("❌ No workflow runs found")
                return False
                
            run_number = runs[0]["databaseId"]  # Use databaseId instead of number
            status = runs[0]["status"]
            
            if status != "completed":
                print(f"⚠️  Latest run {run_number} status: {status}")
                return False
                
            print(f"✅ Found latest run: {run_number}")
        
        # Download the artifact
        # The artifact name uses the run number, but we need the run ID to download
        # Get the run number from the run data
        run_data = None
        if days_back:
            runs = get_workflow_runs(days_back)
            completed_runs = [r for r in runs if r["status"] == "completed"]
            run_data = completed_runs[0]
        else:
            runs = get_workflow_runs(1)
            run_data = runs[0]
            
        artifact_name = f"feast-offline-store-{run_data['number']}"
        print(f"📥 Downloading artifact: {artifact_name}")
        
        # Use full path to gh.exe on Windows
        import platform
        if platform.system() == "Windows":
            gh_cmd = r"C:\Program Files\GitHub CLI\gh.exe"
        else:
            gh_cmd = "gh"
        
        # Clean up temp directory before downloading
        temp_dir = Path("temp_artifacts")
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        
        subprocess.run([
            gh_cmd, "run", "download", str(run_number), 
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
    """Sync downloaded files to local Feast store"""
    print("📦 Syncing data...")
    
    try:
        # Check if temp directory exists
        temp_dir = Path("temp_artifacts")
        if not temp_dir.exists():
            print("❌ No temp_artifacts directory found")
            return False
        
        # GitHub CLI extracts files directly, so we can copy them immediately
        feast_data_dir = Path("feature_repo/data")
        feast_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy parquet file (directly from temp directory)
        parquet_src = temp_dir / "aqi_features.parquet"
        parquet_dst = feast_data_dir / "aqi_features.parquet"
        
        if parquet_src.exists():
            # Check if local parquet file already exists
            if parquet_dst.exists():
                print(f"Existing parquet file found. Merging with new data...")
                
                # Load both dataframes
                import pandas as pd
                existing_df = pd.read_parquet(parquet_dst)
                new_df = pd.read_parquet(parquet_src)
                
                print(f"   Existing records: {len(existing_df)}")
                print(f"   New records: {len(new_df)}")
                print(f"   Existing date range: {existing_df['timestamp'].min()} to {existing_df['timestamp'].max()}")
                print(f"   New date range: {new_df['timestamp'].min()} to {new_df['timestamp'].max()}")
                
                # Merge dataframes, removing duplicates by timestamp (keep newer data)
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                combined_df = combined_df.drop_duplicates(subset=['timestamp'], keep='last')
                combined_df = combined_df.sort_values('timestamp').reset_index(drop=True)
                
                print(f"   Merge complete:")
                print(f"      Total records after merge: {len(combined_df)}")
                print(f"      Records added: {len(combined_df) - len(existing_df)}")
                
                # Save merged data
                combined_df.to_parquet(parquet_dst, index=False)
                print(f"Synced (merged): {parquet_dst}")
            else:
                # No existing file, just copy
                shutil.copy2(parquet_src, parquet_dst)
                print(f"Synced (new): {parquet_dst}")
        else:
            print("No parquet file found in artifact")
        
        # Copy registry file (directly from temp directory)
        registry_src = temp_dir / "registry.db"
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
        print(f"❌ Error syncing: {e}")
        return False

def extract_and_sync_from_dir(temp_dir: Path) -> bool:
    """Sync files from a specified temp directory to local Feast store.
    Reuses the same merge logic as extract_and_sync(), but parameterized by source dir.
    """
    print("📦 Syncing data from", temp_dir)
    try:
        if not temp_dir.exists():
            print(f"❌ No directory found: {temp_dir}")
            return False

        feast_data_dir = Path("feature_repo/data")
        feast_data_dir.mkdir(parents=True, exist_ok=True)

        # Parquet
        parquet_src = temp_dir / "aqi_features.parquet"
        parquet_dst = feast_data_dir / "aqi_features.parquet"

        if parquet_src.exists():
            import pandas as pd
            if parquet_dst.exists():
                print("Existing parquet file found. Merging with new data...")
                existing_df = pd.read_parquet(parquet_dst)
                new_df = pd.read_parquet(parquet_src)
                print(f"   Existing records: {len(existing_df)}")
                print(f"   New records: {len(new_df)}")
                print(f"   Existing date range: {existing_df['timestamp'].min()} to {existing_df['timestamp'].max()}")
                print(f"   New date range: {new_df['timestamp'].min()} to {new_df['timestamp'].max()}")

                combined_df = (
                    pd.concat([existing_df, new_df], ignore_index=True)
                    .drop_duplicates(subset=["timestamp"], keep="last")
                    .sort_values("timestamp")
                    .reset_index(drop=True)
                )
                print("   Merge complete:")
                print(f"      Total records after merge: {len(combined_df)}")
                print(f"      Records added: {len(combined_df) - len(existing_df)}")
                combined_df.to_parquet(parquet_dst, index=False)
                print(f"Synced (merged): {parquet_dst}")
            else:
                shutil.copy2(parquet_src, parquet_dst)
                print(f"Synced (new): {parquet_dst}")
        else:
            print("No parquet file found in artifact directory")

        # Registry: copy last one (optional)
        registry_src = temp_dir / "registry.db"
        registry_dst = feast_data_dir / "registry.db"
        if registry_src.exists():
            shutil.copy2(registry_src, registry_dst)
            print(f"✅ Synced: {registry_dst}")

        return True
    except Exception as e:
        print(f"❌ Error syncing from {temp_dir}: {e}")
        return False

def process_run(run: dict) -> bool:
    """Download and merge artifacts for a single workflow run.
    Expects a dict with keys: databaseId (run id), number (run number), createdAt, status.
    """
    try:
        import platform
        gh_cmd = r"C:\\Program Files\\GitHub CLI\\gh.exe" if platform.system() == "Windows" else "gh"
        run_id = run["databaseId"]
        run_number = run["number"]

        artifact_name = f"feast-offline-store-{run_number}"
        tmp_dir = Path(f"temp_artifacts_{run_id}")
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
        tmp_dir.mkdir(parents=True, exist_ok=True)

        print(f"📥 Downloading artifact for run {run_number} (id={run_id}): {artifact_name}")
        subprocess.run([gh_cmd, "run", "download", str(run_id), "-n", artifact_name, "-D", str(tmp_dir)], check=True)

        ok = extract_and_sync_from_dir(tmp_dir)
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return ok
    except subprocess.CalledProcessError as e:
        print(f"❌ Error downloading artifact for run {run.get('number')}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error processing run {run.get('number')}: {e}")
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
        # Make now timezone-aware to match latest_time
        from datetime import timezone
        now = pd.Timestamp.now(timezone.utc)
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
    import platform
    if platform.system() == "Windows":
        gh_cmd = r"C:\Program Files\GitHub CLI\gh.exe"
    else:
        gh_cmd = "gh"
        
    try:
        subprocess.run([gh_cmd, "--version"], capture_output=True, check=True)
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
    
    # If a time window is requested, iterate through ALL completed runs in that window
    if days_back:
        runs = get_workflow_runs(days_back)
        if not runs:
            print(f"❌ No workflow runs found in the last {days_back} days")
            return

        # Only completed runs
        completed_runs = [r for r in runs if r.get("status") == "completed"]
        if not completed_runs:
            print(f"❌ No completed runs found in the last {days_back} days")
            return

        # Sort oldest → newest by createdAt
        from datetime import timezone
        completed_runs.sort(key=lambda r: datetime.fromisoformat(r["createdAt"].replace("Z", "+00:00")).astimezone(timezone.utc))

        print(f"📦 Processing {len(completed_runs)} completed runs from last {days_back} days (oldest → newest)...")
        processed = 0
        for r in completed_runs:
            print(f"— Processing run {r['number']} created at {r['createdAt']}")
            if process_run(r):
                processed += 1
            else:
                print(f"⚠️  Skipped run {r['number']} due to error")

        print(f"✅ Processed {processed}/{len(completed_runs)} runs")
    else:
        # Single-run paths: latest or explicit run
        if not download_artifact(run_number, days_back):
            return
        if not extract_and_sync():
            return
    
    # Verify
    if not verify_sync():
        return
    
    # Materialize features after successful sync
    print("\n🔄 Materializing features to online store...")
    if not materialize_to_online_store():
        print("⚠️  Sync completed but materialization failed")
        return
    
    print("\n🎉 Sync and materialization completed successfully!")
    print("✅ Your local Feast data is now up to date and materialized")
    
    # Show next steps
    print("\n💡 Next steps:")
    print("   • Run your training pipeline: python training_pipeline.py")
    print("   • Check model performance: cat model_performance_history.csv")
    print("   • Set up daily sync: Add to your daily routine")

if __name__ == "__main__":
    main()
