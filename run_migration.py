import sqlite3
import os
import sys

# Add current dir to path
sys.path.append(os.getcwd())

# Import hashing
try:
    from api.agent.auth import get_password_hash
except ImportError:
    # Fallback if import fails
    print("Could not import auth, using simple implementation for migration")
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    def get_password_hash(password):
        return pwd_context.hash(password)

DB_PATH = '/home/shared_dir/vercel_app/api/data/SQL/kfupm_relational.db'

def run_migration():
    print(f"Migrating database at {DB_PATH} ...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("Created users table.")

    # 2. Create chat_sessions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_sessions (
        id TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        title TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    print("Created chat_sessions table.")

    # 3. Create chat_messages table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES chat_sessions (id)
    )
    ''')
    print("Created chat_messages table.")
    
    # 4. Seed Admin Account
    admin_username = "Kfupmsdaia"
    admin_password = "aerospace"
    admin_role = "admin"
    
    # Check if admin exists
    cursor.execute("SELECT id FROM users WHERE username = ?", (admin_username,))
    if cursor.fetchone() is None:
        print(f"Seeding admin account: {admin_username}")
        hashed_pwd = get_password_hash(admin_password)
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
            (admin_username, hashed_pwd, admin_role)
        )
    else:
        print("Admin account already exists.")

    conn.commit()
    conn.close()
    print("Migration complete successfully.")

if __name__ == "__main__":
    run_migration()
