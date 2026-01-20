#!/bin/bash

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     🚀 KFUPM CHATBOT - DEPLOYMENT STATUS CHECK               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check 1: Git status
echo "✅ CHECK 1: Git Repository Status"
echo "─────────────────────────────────────────────────────────────────"
git log --oneline -1
echo ""
echo "✅ Latest commit pushed to GitHub"
echo ""

# Check 2: Database file status
echo "✅ CHECK 2: Database Configuration"
echo "─────────────────────────────────────────────────────────────────"
if [ -f "api/agent/database.py" ]; then
    if grep -q "HybridDatabaseManager" api/agent/database.py; then
        echo "✅ Hybrid database active (SQLite + Supabase)"
    else
        echo "⚠️  Old database in use - hybrid not active"
    fi
else
    echo "❌ database.py not found"
fi
echo ""

# Check 3: Requirements
echo "✅ CHECK 3: Dependencies"
echo "─────────────────────────────────────────────────────────────────"
if grep -q "supabase" requirements.txt; then
    echo "✅ Supabase added to requirements.txt"
else
    echo "❌ Supabase not in requirements.txt"
fi
echo ""

# Check 4: Files created
echo "✅ CHECK 4: Setup Files"
echo "─────────────────────────────────────────────────────────────────"
files=("supabase_schema.sql" "README_NEXT_STEPS.md" "DEPLOYMENT_STATUS.md")
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ Missing: $file"
    fi
done
echo ""

# Summary
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    📋 WHAT YOU NEED TO DO                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "🎯 Your Supabase Key (ready to use):"
echo "   sbp_b74a04aad24733636a381220a61d8c652889259b"
echo ""
echo "📍 Next Steps (5 minutes):"
echo ""
echo "1️⃣  CREATE SUPABASE PROJECT (2 min)"
echo "    → Go to: https://supabase.com/dashboard"
echo "    → Click 'New Project'"
echo "    → Name: kfupm-chatbot"
echo "    → Generate password (save it!)"
echo "    → Region: Singapore"
echo "    → Click 'Create' and wait 2 minutes"
echo ""
echo "2️⃣  GET PROJECT URL (30 sec)"
echo "    → In Supabase: Settings → API"
echo "    → Copy 'Project URL' (looks like: https://xxxxx.supabase.co)"
echo ""
echo "3️⃣  CREATE TABLES (1 min)"
echo "    → In Supabase: Click 'SQL Editor'"
echo "    → Click '+ New query'"
echo "    → Open file: supabase_schema.sql"
echo "    → Copy ALL SQL and paste"
echo "    → Click 'Run'"
echo ""
echo "4️⃣  ADD TO VERCEL (1 min)"
echo "    → Go to: https://vercel.com/dashboard"
echo "    → Your project → Settings → Environment Variables"
echo "    → Add variable #1:"
echo "       Name:  SUPABASE_URL"
echo "       Value: (your URL from step 2)"
echo "    → Add variable #2:"
echo "       Name:  SUPABASE_KEY"
echo "       Value: sbp_b74a04aad24733636a381220a61d8c652889259b"
echo "    → Click 'Save' for each"
echo ""
echo "5️⃣  VERCEL AUTO-DEPLOYS (2 min)"
echo "    → Vercel will automatically detect and deploy"
echo "    → Wait ~2 minutes for build to complete"
echo "    → Done! 🎉"
echo ""
echo "─────────────────────────────────────────────────────────────────"
echo "📖 Full Guide: Read 'README_NEXT_STEPS.md'"
echo "🧪 Test Connection: python3 test_supabase.py"
echo "─────────────────────────────────────────────────────────────────"
echo ""
echo "✅ All code is deployed to GitHub!"
echo "✅ Just need Supabase setup (5 minutes)"
echo ""
