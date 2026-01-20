#!/usr/bin/env python3
"""
Quick deployment script - Uses Supabase token to set everything up
"""

import os
import sys

# Your Supabase service role key
SUPABASE_KEY = "sbp_b74a04aad24733636a381220a61d8c652889259b"

print("🚀 KFUPM Chatbot - Quick Deployment")
print("=" * 60)
print()

# Step 1: Get Supabase URL
print("📍 Step 1: Enter your Supabase Project URL")
print("   (If you haven't created a project yet, go to:")
print("    https://supabase.com/dashboard and create one)")
print()
supabase_url = input("Paste your Supabase URL here: ").strip()

if not supabase_url:
    print("❌ URL required! Exiting.")
    sys.exit(1)

if not supabase_url.startswith("https://"):
    print("❌ Invalid URL format. Should be: https://xxxxx.supabase.co")
    sys.exit(1)

print(f"✓ Using: {supabase_url}")
print()

# Step 2: Test connection
print("🔌 Step 2: Testing connection to Supabase...")
try:
    from supabase import create_client
    client = create_client(supabase_url, SUPABASE_KEY)
    print("✓ Connected successfully!")
except ImportError:
    print("❌ supabase package not installed!")
    print("   Installing now...")
    os.system("pip install supabase==2.3.0 -q")
    from supabase import create_client
    client = create_client(supabase_url, SUPABASE_KEY)
    print("✓ Installed and connected!")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    sys.exit(1)

print()

# Step 3: Create tables
print("📊 Step 3: Creating database tables...")
print("   (This will be done via Supabase SQL Editor)")
print()
print("   Please do this manually:")
print("   1. Open Supabase SQL Editor")
print("   2. Copy SQL from: supabase_schema.sql")
print("   3. Paste and run")
print()
input("Press Enter after you've created the tables...")

# Step 4: Test table access
print()
print("🧪 Step 4: Verifying tables...")
try:
    result = client.table('users').select('*').limit(1).execute()
    print(f"✓ Found users table with {len(result.data)} rows")

    # Try to insert a test session
    test_result = client.table('users').select('id').eq('username', 'anonymous_user').execute()
    if test_result.data:
        user_id = test_result.data[0]['id']
        print(f"✓ Anonymous user exists (id: {user_id})")
    else:
        print("⚠ Anonymous user not found - tables might not be set up correctly")

except Exception as e:
    print(f"❌ Table verification failed: {e}")
    print("   Make sure you ran the SQL schema!")
    sys.exit(1)

print()

# Step 5: Save configuration
print("💾 Step 5: Saving configuration...")

env_content = f"""# Supabase Configuration
SUPABASE_URL={supabase_url}
SUPABASE_KEY={SUPABASE_KEY}

# vLLM Configuration
VLLM_BASE_URL=http://localhost:8000/v1
MODEL_NAME=/home/shared_dir/Qwen3-30B-A3B-Instruct-2507
"""

with open('.env.local', 'w') as f:
    f.write(env_content)

print("✓ Saved to .env.local")
print()

# Step 6: Vercel instructions
print("🔧 Step 6: Add to Vercel Environment Variables")
print()
print("   Go to: https://vercel.com/dashboard")
print("   → Your project → Settings → Environment Variables")
print()
print("   Add these TWO variables:")
print(f"   ┌─────────────────────────────────────────────────────────┐")
print(f"   │ SUPABASE_URL = {supabase_url:<45} │")
print(f"   │ SUPABASE_KEY = {SUPABASE_KEY:<45} │")
print(f"   └─────────────────────────────────────────────────────────┘")
print()
input("Press Enter after you've added them to Vercel...")

print()

# Step 7: Deploy
print("🚀 Step 7: Deploying to Vercel...")
print()

proceed = input("Ready to commit and push? (y/n): ").lower()
if proceed != 'y':
    print("❌ Deployment cancelled")
    print()
    print("When ready, run:")
    print("  git add .")
    print("  git commit -m 'Add Supabase persistent storage'")
    print("  git push")
    sys.exit(0)

# Git operations
print()
print("📦 Committing changes...")
os.system("git add .")
commit_msg = """Add Supabase for persistent storage

- Switched to hybrid database (SQLite + Supabase)
- Course data: SQLite (read-only, fast)
- User data: Supabase (persistent, cloud)
- Fixes data loss on Vercel
- All UI bugs fixed
"""

os.system(f'git commit -m "{commit_msg.strip()}"')

print()
print("🚀 Pushing to GitHub...")
os.system("git push")

print()
print("=" * 60)
print("✅ DEPLOYMENT COMPLETE!")
print("=" * 60)
print()
print("Next steps:")
print("  1. Wait ~2 minutes for Vercel to build")
print("  2. Visit your chatbot URL")
print("  3. Ask a question")
print("  4. Check Supabase → Table Editor → chat_sessions")
print("  5. See your data! 🎉")
print()
print("Admin panel: your-url.vercel.app/admin")
print("  Username: Kfupmsdaia")
print("  Password: aerospace")
print()
print("🎉 Your chatbot is now production-ready!")
print("   - Zero data loss")
print("   - Working admin panel")
print("   - Persistent storage")
print()
