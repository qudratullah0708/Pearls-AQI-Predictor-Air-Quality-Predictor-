"""
SQLite database for model performance tracking
Replaces CSV with proper database for better querying and indexing
"""

import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

DB_PATH = "model_performance.db"

def init_database():
    """Initialize the performance tracking database with proper schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create performance history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS model_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            horizon TEXT NOT NULL,
            model TEXT NOT NULL,
            mae REAL NOT NULL,
            rmse REAL NOT NULL,
            r2 REAL NOT NULL,
            mape REAL NOT NULL,
            n_test_samples INTEGER NOT NULL,
            deployed BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create indexes for faster queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_horizon 
        ON model_performance(horizon)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_timestamp 
        ON model_performance(timestamp DESC)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_horizon_model 
        ON model_performance(horizon, model)
    """)
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized: {DB_PATH}")


@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


def save_performance_result(result):
    """Save a single performance result to the database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO model_performance 
            (timestamp, horizon, model, mae, rmse, r2, mape, n_test_samples, deployed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result['timestamp'],
            result['horizon'],
            result['model'],
            result['mae'],
            result['rmse'],
            result['r2'],
            result['mape'],
            result['n_test_samples'],
            result.get('deployed', 0)
        ))
        conn.commit()


def get_latest_performance(horizon, model_name=None):
    """Get latest performance for a specific horizon and model"""
    with get_db_connection() as conn:
        query = """
            SELECT * FROM model_performance 
            WHERE horizon = ?
        """
        params = [horizon]
        
        if model_name:
            query += " AND model = ?"
            params.append(model_name)
        
        query += " ORDER BY timestamp DESC LIMIT 1"
        
        df = pd.read_sql_query(query, conn, params=params)
        return df


def get_best_model_for_horizon(horizon):
    """Get the best model (lowest RMSE) for a specific horizon"""
    with get_db_connection() as conn:
        query = """
            SELECT * FROM model_performance 
            WHERE horizon = ?
            ORDER BY timestamp DESC, rmse ASC
            LIMIT 1
        """
        df = pd.read_sql_query(query, conn, params=[horizon])
        return df


def get_performance_history(horizon, limit=10, model_name=None):
    """Get historical performance data for a horizon"""
    with get_db_connection() as conn:
        query = """
            SELECT * FROM model_performance 
            WHERE horizon = ?
        """
        params = [horizon]
        
        if model_name:
            query += " AND model = ?"
            params.append(model_name)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        df = pd.read_sql_query(query, conn, params=params)
        return df


def get_all_performance():
    """Get all performance data"""
    with get_db_connection() as conn:
        return pd.read_sql_query("SELECT * FROM model_performance ORDER BY timestamp DESC", conn)


def mark_as_deployed(horizon, model, timestamp):
    """Mark a model as deployed"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE model_performance 
            SET deployed = 1 
            WHERE horizon = ? AND model = ? AND timestamp = ?
        """, (horizon, model, timestamp))
        conn.commit()


def migrate_csv_to_db():
    """Migrate existing CSV data to SQLite database"""
    csv_path = Path("model_performance_history.csv")
    
    if not csv_path.exists():
        print("⚠️  No CSV file found to migrate")
        return
    
    try:
        # Read CSV
        df = pd.read_csv(csv_path)
        
        # Add deployed column if it doesn't exist
        if 'deployed' not in df.columns:
            df['deployed'] = 0
        
        # Initialize database
        init_database()
        
        # Insert data
        with get_db_connection() as conn:
            # Check if data already exists
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM model_performance")
            existing_count = cursor.fetchone()[0]
            
            if existing_count > 0:
                print(f"⚠️  Database already has {existing_count} records. Skipping migration.")
                return
            
            # Insert all rows
            df.to_sql('model_performance', conn, if_exists='append', index=False)
            conn.commit()
        
        print(f"✅ Migrated {len(df)} records from CSV to SQLite database")
        
    except Exception as e:
        print(f"❌ Error migrating CSV data: {e}")


if __name__ == "__main__":
    # Initialize database
    init_database()
    
    # Migrate CSV data if it exists
    migrate_csv_to_db()
    
    print("\n✅ Performance database setup complete!")

