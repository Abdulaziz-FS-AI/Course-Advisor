import sqlite3
import os

DB_PATH = "/home/shared_dir/vercel_app/api/data/SQL/kfupm_relational.db"

def inspect_db():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Get tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cur.fetchall() if not t[0].startswith('sqlite_')]
    
    print(f"{'Table Name':<25} | {'Row Count':<10}")
    print("-" * 40)
    
    for table in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"{table:<25} | {count:<10}")
        except Exception as e:
            print(f"{table:<25} | Error: {e}")

    print("\n--- Schema Highlights ---")
    for table in ['departments', 'courses', 'program_plans']:
        if table in tables:
            print(f"\n[{table} columns]:")
            cur.execute(f"PRAGMA table_info({table})")
            columns = [c[1] for c in cur.fetchall()]
            print(", ".join(columns))

    conn.close()

if __name__ == "__main__":
    inspect_db()
