# Quick Guide: Migrate to Vercel Postgres

## Step 1: Create Vercel Postgres Database

1. Go to https://vercel.com/dashboard
2. Select your project
3. Click **Storage** tab
4. Click **Create Database**
5. Select **Postgres**
6. Choose a name (e.g., "kfupm-chatbot-db")
7. Select region closest to users
8. Click **Create**

## Step 2: Get Connection String

After creation, Vercel will show environment variables:
- `POSTGRES_URL`
- `POSTGRES_PRISMA_URL`
- `POSTGRES_URL_NON_POOLING`

These are **automatically** added to your Vercel project.

## Step 3: Install Dependencies

Add to `requirements.txt`:
```
psycopg2-binary==2.9.9
```

## Step 4: Update database.py

Replace the `DatabaseManager.__init__` method:

```python
def __init__(self, db_path: Path = DB_PATH):
    import os

    # Check if we have Postgres env var (Vercel)
    postgres_url = os.getenv("POSTGRES_URL")

    if postgres_url:
        print(f"✓ Using Vercel Postgres")
        self.db_type = "postgres"
        self.conn_string = postgres_url
        self._init_postgres_schema()
    else:
        print(f"Local mode - using SQLite: {db_path}")
        self.db_type = "sqlite"
        self.db_path = db_path
        self._validate_database()
```

## Step 5: Add Postgres Connection Method

```python
@contextmanager
def get_connection(self):
    """Context manager for database connections."""
    if self.db_type == "postgres":
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(self.conn_string)
        conn.cursor_factory = psycopg2.extras.RealDictCursor
    else:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row

    try:
        yield conn
    finally:
        conn.close()
```

## Step 6: Create Schema Migration Script

```python
# scripts/migrate_to_postgres.py
import psycopg2
import os

# Get connection string from Vercel env
conn = psycopg2.connect(os.getenv("POSTGRES_URL"))
cur = conn.cursor()

# Create tables
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS chat_sessions (
    id TEXT PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    device_id TEXT,
    title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    session_id TEXT REFERENCES chat_sessions(id),
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_id TEXT,
    message_id INTEGER REFERENCES chat_messages(id),
    rating TEXT CHECK(rating IN ('up','down')),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

# Create indexes
cur.execute("CREATE INDEX IF NOT EXISTS idx_sessions_device ON chat_sessions(device_id);")
cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON chat_messages(session_id);")
cur.execute("CREATE INDEX IF NOT EXISTS idx_feedback_session ON feedback(session_id);")

conn.commit()
cur.close()
conn.close()

print("✓ Postgres schema created!")
```

## Step 7: Deploy

```bash
git add .
git commit -m "Migrate to Vercel Postgres"
git push
```

Vercel will automatically:
1. Install `psycopg2-binary`
2. Connect to your Postgres database
3. Your data will now persist! 🎉

## Testing

1. Deploy to Vercel
2. Ask a question on the chatbot
3. Wait 20 minutes (let function restart)
4. Refresh page
5. **Your chat should still be there!**

## Rollback (If Needed)

The code will automatically fall back to SQLite if `POSTGRES_URL` is not set, so local development continues to work.

---

**Estimated time:** 30 minutes
**Difficulty:** Medium
