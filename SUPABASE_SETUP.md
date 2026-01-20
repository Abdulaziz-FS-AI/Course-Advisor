# 🚀 Setup Supabase for Chat & Feedback (BEST SOLUTION!)

## Why This Approach?

**Hybrid storage:**
- 📚 **SQLite** → Course data (read-only, works perfectly in /tmp)
- 💬 **Supabase** → Chat sessions, messages, feedback (persistent, cloud-based)

**Benefits:**
- ✅ Free tier: 500MB storage, unlimited API requests
- ✅ No data loss on Vercel restarts
- ✅ Easy setup (15 minutes)
- ✅ Automatic backups
- ✅ Real-time updates possible

---

## Step 1: Create Supabase Project

1. Go to https://supabase.com
2. Click **"Start your project"** → Sign up (GitHub login works)
3. Click **"New Project"**
4. Fill in:
   - **Name:** kfupm-chatbot
   - **Database Password:** (Generate strong password, save it!)
   - **Region:** Choose closest to your users
5. Click **"Create new project"** (takes ~2 minutes)

---

## Step 2: Create Database Tables

1. In Supabase dashboard, go to **SQL Editor**
2. Click **"New query"**
3. Paste this SQL:

```sql
-- Users table
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create anonymous user
INSERT INTO users (username, password_hash, role)
VALUES ('anonymous_user', 'nopassword', 'user')
ON CONFLICT (username) DO NOTHING;

-- Chat sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id TEXT PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    device_id TEXT,
    title TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for faster device queries
CREATE INDEX IF NOT EXISTS idx_sessions_device ON chat_sessions(device_id);
CREATE INDEX IF NOT EXISTS idx_sessions_updated ON chat_sessions(updated_at DESC);

-- Chat messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for faster session message retrieval
CREATE INDEX IF NOT EXISTS idx_messages_session ON chat_messages(session_id);

-- Feedback table
CREATE TABLE IF NOT EXISTS feedback (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    session_id TEXT,
    message_id BIGINT REFERENCES chat_messages(id) ON DELETE CASCADE,
    rating TEXT CHECK(rating IN ('up', 'down')),
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for faster feedback queries
CREATE INDEX IF NOT EXISTS idx_feedback_session ON feedback(session_id);
CREATE INDEX IF NOT EXISTS idx_feedback_created ON feedback(created_at DESC);
```

4. Click **"Run"**
5. You should see: "Success. No rows returned"

---

## Step 3: Get API Credentials

1. Go to **Project Settings** (⚙️ icon bottom left)
2. Click **API** in sidebar
3. Copy these values:

   - **Project URL:** `https://xxxxx.supabase.co`
   - **anon public key:** `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
   - **service_role key:** `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (⚠️ Keep secret!)

---

## Step 4: Add to Vercel Environment Variables

1. Go to your Vercel project dashboard
2. Click **Settings** → **Environment Variables**
3. Add these:

   | Name | Value |
   |------|-------|
   | `SUPABASE_URL` | `https://xxxxx.supabase.co` |
   | `SUPABASE_KEY` | Your `service_role` key (long JWT token) |

4. Click **Save**
5. **Redeploy** your project to apply changes

---

## Step 5: Update Requirements

Add to `requirements.txt`:

```
supabase==2.3.0
```

---

## Step 6: Test Locally

Create `.env` file in project root:

```bash
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your_service_role_key
VLLM_BASE_URL=http://localhost:8000/v1
```

Test connection:

```bash
cd /home/shared_dir/Kfupm_Chatbot
python3 -c "
import os
from supabase import create_client

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')

client = create_client(url, key)
result = client.table('users').select('*').execute()
print(f'✓ Connected! Found {len(result.data)} users')
"
```

You should see: `✓ Connected! Found 1 users`

---

## Step 7: Deploy

The modified `database.py` will automatically:
- Use Supabase for chat/feedback on Vercel
- Use SQLite for course data (read-only)
- Fall back to SQLite for everything locally

```bash
git add .
git commit -m "Add Supabase for persistent chat storage"
git push
```

---

## Verification

1. **Ask a question** on your chatbot
2. **Check Supabase** dashboard → Table Editor → `chat_sessions`
3. You should see the session!
4. **Wait 30 minutes** (let Vercel restart)
5. **Refresh** your chatbot
6. **Your chat history is still there!** 🎉

---

## Admin Panel

Now your admin panel will show **all** user sessions and feedback persistently!

**Login:** https://your-domain.vercel.app/admin
- Username: `Kfupmsdaia`
- Password: `aerospace`

---

## Troubleshooting

### "Connection refused"
- Check `SUPABASE_URL` is correct (no trailing slash)
- Check `SUPABASE_KEY` is the `service_role` key, not `anon`

### "Table does not exist"
- Run the SQL from Step 2 again in Supabase SQL Editor

### "No data showing in admin"
- Check Vercel logs: `vercel logs`
- Look for: `✓ Using Supabase for chat/feedback`

---

## Cost

**Free tier:**
- 500MB database
- 1GB file storage
- Unlimited API requests
- Auto-pause after 1 week inactivity

**Pro tier ($25/month):**
- Only needed if you exceed free tier limits

---

## Next Steps

After setup:
1. The code I've created will handle everything automatically
2. SQLite still used for course queries (fast, local)
3. Supabase used for all chat/feedback (persistent, cloud)
4. Zero data loss on Vercel! 🚀
