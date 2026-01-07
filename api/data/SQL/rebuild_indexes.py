import sqlite3
import os

DB_PATH = "/home/shared_dir/vercel_app/api/data/SQL/kfupm_relational.db"

def rebuild_indexes():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    try:
        print("Starting index rebuild...")
        
        # 1. Departments FTS
        print("Rebuilding departments_fts...")
        cur.executescript("""
            DROP TABLE IF EXISTS departments_fts;
            CREATE VIRTUAL TABLE departments_fts USING fts5(
                id UNINDEXED,
                name,
                shortcut,
                tokenize='trigram'
            );
            INSERT INTO departments_fts(id, name, shortcut)
            SELECT id, name, shortcut FROM departments;
        """)
        
        # 2. Courses FTS
        print("Rebuilding courses_fts...")
        cur.executescript("""
            DROP TABLE IF EXISTS courses_fts;
            CREATE VIRTUAL TABLE courses_fts USING fts5(
                id UNINDEXED,
                code,
                title,
                description,
                tokenize='trigram'
            );
            INSERT INTO courses_fts(id, code, title, description)
            SELECT id, code, title, description FROM courses;
        """)
        
        # 3. Optimize
        print("Optimizing indexes...")
        cur.execute("INSERT INTO departments_fts(departments_fts) VALUES('optimize');")
        cur.execute("INSERT INTO courses_fts(courses_fts) VALUES('optimize');")
        
        conn.commit()
        print("SUCCESS: Tables updated. Now optimizing database file...")
        
    except Exception as e:
        print(f"Error during rebuild: {e}")
        conn.rollback()
    finally:
        conn.close()

    # VACUUM must be run outside of a transaction
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("VACUUM")
        conn.execute("ANALYZE")
        
        # Final Verification
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM courses_fts")
        c_count = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM departments_fts")
        d_count = cur.fetchone()[0]
        print(f"Final Verification: courses_fts={c_count}, departments_fts={d_count}")
        conn.close()
        print("Maintenance complete.")
    except Exception as e:
        print(f"Optimization error: {e}")

if __name__ == "__main__":
    rebuild_indexes()
