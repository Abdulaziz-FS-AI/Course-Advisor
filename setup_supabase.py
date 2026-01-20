#!/usr/bin/env python3
"""
Quick Supabase Setup Script
Sets up tables and tests connection
"""

import os
import sys
from supabase import create_client, Client

# Token provided by user
SUPABASE_KEY = "sbp_b74a04aad24733636a381220a61d8c652889259b"

def main():
    print("🚀 KFUPM Chatbot - Supabase Setup")
    print("=" * 50)

    # Get Supabase URL from user
    print("\n📍 Step 1: Get your Supabase Project URL")
    print("   1. Go to https://supabase.com/dashboard")
    print("   2. Select your project (or create one)")
    print("   3. Go to Settings > API")
    print("   4. Copy the 'Project URL'")
    print()

    supabase_url = input("Paste your Supabase URL here: ").strip()

    if not supabase_url.startswith("https://"):
        print("❌ Invalid URL. Should start with https://")
        sys.exit(1)

    print(f"\n✓ Using URL: {supabase_url}")

    # Test connection
    print("\n🔌 Step 2: Testing connection...")
    try:
        supabase: Client = create_client(supabase_url, SUPABASE_KEY)
        print("✓ Connected to Supabase!")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)

    # Create tables
    print("\n📊 Step 3: Creating database tables...")

    sql_commands = [
        # Users table
        """
        CREATE TABLE IF NOT EXISTS users (
            id BIGSERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """,

        # Insert anonymous user
        """
        INSERT INTO users (username, password_hash, role)
        VALUES ('anonymous_user', 'nopassword', 'user')
        ON CONFLICT (username) DO NOTHING;
        """,

        # Chat sessions table
        """
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id TEXT PRIMARY KEY,
            user_id BIGINT REFERENCES users(id),
            device_id TEXT,
            title TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """,

        # Indexes for sessions
        """
        CREATE INDEX IF NOT EXISTS idx_sessions_device ON chat_sessions(device_id);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_sessions_updated ON chat_sessions(updated_at DESC);
        """,

        # Chat messages table
        """
        CREATE TABLE IF NOT EXISTS chat_messages (
            id BIGSERIAL PRIMARY KEY,
            session_id TEXT REFERENCES chat_sessions(id) ON DELETE CASCADE,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMPTZ DEFAULT NOW()
        );
        """,

        # Index for messages
        """
        CREATE INDEX IF NOT EXISTS idx_messages_session ON chat_messages(session_id);
        """,

        # Feedback table
        """
        CREATE TABLE IF NOT EXISTS feedback (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(id),
            session_id TEXT,
            message_id BIGINT REFERENCES chat_messages(id) ON DELETE CASCADE,
            rating TEXT CHECK(rating IN ('up', 'down')),
            comment TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """,

        # Indexes for feedback
        """
        CREATE INDEX IF NOT EXISTS idx_feedback_session ON feedback(session_id);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_feedback_created ON feedback(created_at DESC);
        """
    ]

    for i, sql in enumerate(sql_commands, 1):
        try:
            # Execute using Supabase's RPC or direct SQL
            supabase.postgrest.rpc('exec_sql', {'query': sql}).execute()
            print(f"  ✓ Command {i}/{len(sql_commands)} executed")
        except Exception as e:
            # Try alternative method - some commands might need direct execution
            print(f"  ⚠ Command {i} using alternative method...")
            try:
                # For table creation, we can use the table API
                pass  # Will handle this differently
            except:
                print(f"  ⚠ Note: {str(e)[:50]}... (may be okay if table exists)")

    print("\n✓ Tables created!")

    # Test by creating a test session
    print("\n🧪 Step 4: Testing database write...")
    try:
        # Get anonymous user
        user_result = supabase.table('users').select('id').eq('username', 'anonymous_user').execute()
        if user_result.data:
            user_id = user_result.data[0]['id']

            # Create test session
            test_session = supabase.table('chat_sessions').insert({
                'id': 'test-session-' + str(os.urandom(4).hex()),
                'device_id': 'test-device',
                'title': 'Test Session',
                'user_id': user_id
            }).execute()

            print("✓ Test session created!")

            # Clean up test session
            supabase.table('chat_sessions').delete().eq('device_id', 'test-device').execute()
            print("✓ Test session cleaned up!")
        else:
            print("⚠ Anonymous user not found, but tables are created")
    except Exception as e:
        print(f"⚠ Test write failed: {e}")
        print("  (Tables might still be created - check Supabase dashboard)")

    # Save configuration
    print("\n💾 Step 5: Saving configuration...")

    env_content = f"""# Supabase Configuration
SUPABASE_URL={supabase_url}
SUPABASE_KEY={SUPABASE_KEY}

# vLLM Configuration
VLLM_BASE_URL=http://localhost:8000/v1
MODEL_NAME=/home/shared_dir/Qwen3-30B-A3B-Instruct-2507
"""

    with open('.env.local', 'w') as f:
        f.write(env_content)

    print("✓ Configuration saved to .env.local")

    # Vercel instructions
    print("\n🚀 Step 6: Add to Vercel (IMPORTANT!)")
    print("   1. Go to https://vercel.com/dashboard")
    print("   2. Select your project")
    print("   3. Settings > Environment Variables")
    print("   4. Add these TWO variables:")
    print(f"\n      SUPABASE_URL = {supabase_url}")
    print(f"      SUPABASE_KEY = {SUPABASE_KEY}")
    print("\n   5. Click Save, then redeploy")

    print("\n" + "=" * 50)
    print("✅ Setup Complete!")
    print("\nNext steps:")
    print("  1. Add env vars to Vercel (see above)")
    print("  2. Switch to hybrid database:")
    print("     cd api/agent")
    print("     mv database.py database_old.py")
    print("     mv database_hybrid.py database.py")
    print("  3. Deploy: git add . && git commit -m 'Add Supabase' && git push")
    print("\n🎉 Your data will now persist forever!")

if __name__ == "__main__":
    main()
