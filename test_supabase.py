#!/usr/bin/env python3
"""
Quick test to verify Supabase connection
"""

import os
import sys

# Your Supabase service role key
SUPABASE_KEY = "sbp_b74a04aad24733636a381220a61d8c652889259b"

def test_connection(supabase_url):
    """Test connection to Supabase"""
    try:
        from supabase import create_client
        print(f"🔌 Testing connection to: {supabase_url}")

        client = create_client(supabase_url, SUPABASE_KEY)

        # Try to query users table
        result = client.table('users').select('*').limit(1).execute()

        print("✅ SUCCESS! Connected to Supabase!")
        print(f"   Found {len(result.data)} user(s) in database")
        return True

    except ImportError:
        print("❌ ERROR: supabase-py not installed")
        print("   Run: pip install supabase==2.3.0")
        return False

    except Exception as e:
        error_msg = str(e)

        if "relation" in error_msg and "does not exist" in error_msg:
            print("⚠️  Tables don't exist yet")
            print("   → Go to Supabase SQL Editor")
            print("   → Run the SQL from supabase_schema.sql")
            return False

        elif "Invalid" in error_msg or "401" in error_msg:
            print("❌ Authentication failed")
            print("   → Check your SUPABASE_KEY is correct")
            return False

        else:
            print(f"❌ Connection failed: {error_msg}")
            return False

if __name__ == "__main__":
    print("🚀 KFUPM Chatbot - Supabase Connection Test")
    print("=" * 60)

    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        print("\n📍 Enter your Supabase Project URL")
        print("   (Go to Supabase Dashboard → Settings → API)")
        print()
        url = input("Paste URL here: ").strip()

    if not url.startswith("https://"):
        print("❌ Invalid URL. Should be: https://xxxxx.supabase.co")
        sys.exit(1)

    print()
    success = test_connection(url)
    print()

    if success:
        print("✅ All good! You can now deploy!")
        print("\nNext steps:")
        print("  1. Add to Vercel env vars:")
        print(f"     SUPABASE_URL={url}")
        print(f"     SUPABASE_KEY={SUPABASE_KEY}")
        print("  2. Deploy: git push")
        print("  3. Your data will persist! 🎉")
    else:
        print("❌ Fix the issues above and try again")
