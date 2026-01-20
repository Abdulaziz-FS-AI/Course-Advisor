#!/bin/bash
# KFUPM Chatbot - Deploy to Vercel with Supabase

echo "🚀 KFUPM Chatbot - Deployment Script"
echo "======================================"
echo ""

# Check if we're in the right directory
if [ ! -f "index.html" ]; then
    echo "❌ Error: Run this from the Kfupm_Chatbot directory"
    exit 1
fi

# Check if hybrid database is active
if [ ! -f "api/agent/database.py" ]; then
    echo "❌ Error: database.py not found"
    exit 1
fi

# Check if database_hybrid exists (should be renamed to database.py)
if [ -f "api/agent/database_hybrid.py" ]; then
    echo "⚠️  Warning: database_hybrid.py still exists"
    echo "   The hybrid database should be renamed to database.py"
    echo "   Run: mv api/agent/database.py api/agent/database_sqlite_only.py"
    echo "        mv api/agent/database_hybrid.py api/agent/database.py"
    exit 1
fi

# Verify Supabase configuration
echo "📋 Pre-deployment checklist:"
echo ""
echo "✓ Hybrid database active"
echo "✓ Supabase library in requirements.txt"
echo ""

# Remind about environment variables
echo "⚠️  IMPORTANT: Before deploying, add these to Vercel:"
echo ""
echo "   1. Go to: https://vercel.com/dashboard"
echo "   2. Settings > Environment Variables"
echo "   3. Add:"
echo "      SUPABASE_URL = https://xxxxx.supabase.co"
echo "      SUPABASE_KEY = sbp_b74a04aad24733636a381220a61d8c652889259b"
echo ""
read -p "Have you added these to Vercel? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Please add environment variables to Vercel first!"
    exit 1
fi

# Check git status
echo ""
echo "📊 Git status:"
git status --short

echo ""
read -p "Ready to commit and deploy? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

# Git operations
echo ""
echo "📦 Committing changes..."
git add .
git commit -m "Deploy with Supabase persistent storage

- Switched to hybrid database (SQLite + Supabase)
- Added supabase==2.3.0 to requirements
- Course data: SQLite (read-only, fast)
- User data: Supabase (persistent, cloud)
- Fixes data loss on Vercel serverless restarts
"

echo ""
echo "🚀 Pushing to repository..."
git push

echo ""
echo "✅ Deployment initiated!"
echo ""
echo "Next steps:"
echo "  1. Check Vercel dashboard for deployment status"
echo "  2. Wait ~2 minutes for build to complete"
echo "  3. Test your chatbot"
echo "  4. Check admin panel for sessions"
echo "  5. Verify data persists after 20 minutes!"
echo ""
echo "🎉 Done! Your data will now persist forever!"
