"""
Model Performance Tracking Dashboard
Visualizes model performance improvements over time
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

def load_performance_data():
    """Load model performance history"""
    try:
        if not os.path.exists('model_performance_history.csv'):
            print("❌ No performance history found. Run training pipeline first.")
            return None
        
        df = pd.read_csv('model_performance_history.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        print(f"✅ Loaded {len(df)} performance records")
        print(f"📅 Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        
        return df
    except Exception as e:
        print(f"❌ Error loading performance data: {e}")
        return None

def create_performance_plots(df):
    """Create performance visualization plots"""
    print("📊 Creating performance plots...")
    
    try:
        # Create outputs directory
        os.makedirs('outputs', exist_ok=True)
        
        # Set style
        plt.style.use('seaborn-v0_8')
        
        # Plot 1: MAE over time for each horizon
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        
        horizons = ['24h', '48h', '72h']
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
        
        for i, horizon in enumerate(horizons):
            horizon_data = df[df['horizon'] == horizon]
            
            if len(horizon_data) == 0:
                axes[i].text(0.5, 0.5, f'No data for {horizon}', 
                           ha='center', va='center', transform=axes[i].transAxes)
                axes[i].set_title(f'MAE Over Time - {horizon}')
                continue
            
            for model in horizon_data['model'].unique():
                model_data = horizon_data[horizon_data['model'] == model]
                axes[i].plot(model_data['timestamp'], model_data['mae'], 
                           marker='o', label=model, linewidth=2, markersize=6)
            
            axes[i].set_title(f'MAE Over Time - {horizon}', fontsize=14, fontweight='bold')
            axes[i].set_xlabel('Training Date')
            axes[i].set_ylabel('MAE (lower is better)')
            axes[i].legend()
            axes[i].grid(True, alpha=0.3)
            
            # Rotate x-axis labels
            axes[i].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig('outputs/performance_trends_mae.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✅ MAE trends plot saved: outputs/performance_trends_mae.png")
        
        # Plot 2: R² over time
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        
        for i, horizon in enumerate(horizons):
            horizon_data = df[df['horizon'] == horizon]
            
            if len(horizon_data) == 0:
                axes[i].text(0.5, 0.5, f'No data for {horizon}', 
                           ha='center', va='center', transform=axes[i].transAxes)
                axes[i].set_title(f'R² Over Time - {horizon}')
                continue
            
            for model in horizon_data['model'].unique():
                model_data = horizon_data[horizon_data['model'] == model]
                axes[i].plot(model_data['timestamp'], model_data['r2'], 
                           marker='s', label=model, linewidth=2, markersize=6)
            
            axes[i].set_title(f'R² Over Time - {horizon}', fontsize=14, fontweight='bold')
            axes[i].set_xlabel('Training Date')
            axes[i].set_ylabel('R² Score (higher is better)')
            axes[i].legend()
            axes[i].grid(True, alpha=0.3)
            axes[i].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig('outputs/performance_trends_r2.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✅ R² trends plot saved: outputs/performance_trends_r2.png")
        
        # Plot 3: Model comparison (latest performance)
        latest_data = df.groupby(['horizon', 'model']).last().reset_index()
        
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        
        for i, horizon in enumerate(horizons):
            horizon_latest = latest_data[latest_data['horizon'] == horizon]
            
            if len(horizon_latest) == 0:
                axes[i].text(0.5, 0.5, f'No data for {horizon}', 
                           ha='center', va='center', transform=axes[i].transAxes)
                axes[i].set_title(f'Latest Performance - {horizon}')
                continue
            
            # Create grouped bar chart
            x_pos = range(len(horizon_latest))
            models = horizon_latest['model'].tolist()
            mae_values = horizon_latest['mae'].tolist()
            r2_values = horizon_latest['r2'].tolist()
            
            # Plot MAE (left axis)
            ax1 = axes[i]
            bars1 = ax1.bar([x - 0.2 for x in x_pos], mae_values, 0.4, 
                          label='MAE', color='lightcoral', alpha=0.7)
            ax1.set_xlabel('Model')
            ax1.set_ylabel('MAE', color='red')
            ax1.tick_params(axis='y', labelcolor='red')
            ax1.set_xticks(x_pos)
            ax1.set_xticklabels(models, rotation=45)
            
            # Plot R² (right axis)
            ax2 = ax1.twinx()
            bars2 = ax2.bar([x + 0.2 for x in x_pos], r2_values, 0.4, 
                          label='R²', color='lightblue', alpha=0.7)
            ax2.set_ylabel('R²', color='blue')
            ax2.tick_params(axis='y', labelcolor='blue')
            
            axes[i].set_title(f'Latest Performance - {horizon}', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig('outputs/latest_performance_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✅ Latest performance comparison saved: outputs/latest_performance_comparison.png")
        
    except Exception as e:
        print(f"❌ Error creating plots: {e}")

def print_performance_summary(df):
    """Print performance summary statistics"""
    print("\n" + "="*60)
    print("📊 MODEL PERFORMANCE SUMMARY")
    print("="*60)
    
    try:
        # Latest performance for each horizon and model
        latest_data = df.groupby(['horizon', 'model']).last().reset_index()
        
        for horizon in ['24h', '48h', '72h']:
            horizon_data = latest_data[latest_data['horizon'] == horizon]
            
            if len(horizon_data) == 0:
                print(f"\n{horizon} ahead predictions: No data available")
                continue
            
            print(f"\n🎯 {horizon} ahead predictions:")
            
            # Find best model (lowest MAE)
            best_model = horizon_data.loc[horizon_data['mae'].idxmin()]
            
            print(f"   🏆 Best Model: {best_model['model']}")
            print(f"      MAE: {best_model['mae']:.2f}")
            print(f"      RMSE: {best_model['rmse']:.2f}")
            print(f"      R²: {best_model['r2']:.3f}")
            print(f"      MAPE: {best_model['mape']:.1f}%")
            
            print(f"   📊 All Models:")
            for _, row in horizon_data.iterrows():
                print(f"      {row['model']:15} MAE: {row['mae']:6.2f}  R²: {row['r2']:6.3f}")
        
        # Performance improvement over time
        print(f"\n📈 Performance Improvement Analysis:")
        
        for horizon in ['24h', '48h', '72h']:
            horizon_data = df[df['horizon'] == horizon]
            
            if len(horizon_data) < 2:
                continue
            
            # Find best model for this horizon
            best_model_name = horizon_data.groupby('model')['mae'].mean().idxmin()
            best_model_data = horizon_data[horizon_data['model'] == best_model_name]
            
            if len(best_model_data) >= 2:
                first_mae = best_model_data['mae'].iloc[0]
                latest_mae = best_model_data['mae'].iloc[-1]
                improvement = ((first_mae - latest_mae) / first_mae) * 100
                
                print(f"   {horizon} ({best_model_name}): {improvement:+.1f}% MAE change")
        
    except Exception as e:
        print(f"❌ Error generating summary: {e}")

def main():
    """Main function"""
    print("🚀 Model Performance Tracking Dashboard")
    print("="*60)
    
    # Load data
    df = load_performance_data()
    if df is None:
        return
    
    # Create visualizations
    create_performance_plots(df)
    
    # Print summary
    print_performance_summary(df)
    
    print(f"\n🎉 Dashboard completed!")
    print(f"📁 Check outputs/ directory for visualization files")
    print(f"💡 Run this script regularly to track model improvements")

if __name__ == "__main__":
    main()
