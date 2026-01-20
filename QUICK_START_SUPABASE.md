# ⚡ Quick Start: Fix Data Persistence with Supabase (15 minutes)

## What You'll Get

✅ **No more data loss** - Sessions and feedback persist forever
✅ **Works on Vercel** - No /tmp issues
✅ **Admin panel shows real data** - See all user conversations
✅ **Free tier** - 500MB storage, unlimited API requests

---

## Step 1: Create Supabase Account (2 min)

1. Go to https://supabase.com
2. Click "Start your project"
3. Sign up with GitHub (easiest)

---

## Step 2: Create Project (2 min)

1. Click "New Project"
2. Fill in:
   - Name: `kfupm-chatbot`
   - Database Password: **(Click generate, then copy it somewhere safe!)**
   - Region: `Southeast Asia (Singapore)` or closest to your users
3. Click "Create new project"
4. **Wait ~2 minutes** for setup to complete

---

## Step 3: Create Tables (1 min)

1. In Supabase, click **"SQL Editor"** (left sidebar)
2. Click **"+ New query"**
3. **Copy and paste this entire SQL block:**

```sql
-- Users table
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create anonymous user
INSERT INTO users (username, password_hash, role)
VALUES ('anonymous_user', 'nopassword', 'user');

-- Chat sessions
CREATE TABLE chat_sessions (
    id TEXT PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    device_id TEXT,
    title TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sessions_device ON chat_sessions(device_id);
CREATE INDEX idx_sessions_updated ON chat_sessions(updated_at DESC);

-- Chat messages
CREATE TABLE chat_messages (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_messages_session ON chat_messages(session_id);

-- Feedback
CREATE TABLE feedback (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    session_id TEXT,
    message_id BIGINT REFERENCES chat_messages(id) ON DELETE CASCADE,
    rating TEXT CHECK(rating IN ('up', 'down')),
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_feedback_session ON feedback(session_id);
```

4. Click **"Run"** (bottom right)
5. Should say: "Success. No rows returned" ✅

---

## Step 4: Get API Keys (1 min)

1. Click **⚙️ Settings** (bottom left)
2. Click **"API"** in sidebar
3. Find and copy these 2 values:

   **A. Project URL**
   ```
   https://xxxxxxxxx.supabase.co
   ```

   **B. service_role key** (NOT anon key!)
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ey...  (very long)
   ```

⚠️ **Important:** Use the `service_role` key (second one), NOT the `anon` key!

---

## Step 5: Add to Vercel (3 min)

1. Go to https://vercel.com/dashboard
2. Select your KFUPM chatbot project
3. Click **Settings** → **Environment Variables**
4. Add **TWO** new variables:

   | Variable Name | Value |
   |--------------|-------|
   | `SUPABASE_URL` | `https://xxxxx.supabase.co` (from step 4A) |
   | `SUPABASE_KEY` | `eyJhbGci...` (from step 4B - the LONG key) |

5. Click **Save** after each

---

## Step 6: Enable Hybrid Database (2 min)

In your project, rename the database file:

```bash
cd /home/shared_dir/Kfupm_Chatbot/api/agent
mv database.py database_old.py
mv database_hybrid.py database.py
```

---

## Step 7: Deploy (2 min)

```bash
cd /home/shared_dir/Kfupm_Chatbot
git add .
git commit -m "Add Supabase for persistent storage"
git push
```

Vercel will automatically redeploy (takes ~1-2 minutes).

---

## Step 8: Test! (2 min)

1. **Go to your chatbot** (your-domain.vercel.app)
2. **Ask a question** (e.g., "What are the SWE courses?")
3. **Wait 20 minutes** (grab coffee ☕)
4. **Refresh the page**
5. **Your chat should still be there!** 🎉

### Also Test Admin Panel:

1. Go to `your-domain.vercel.app/admin`
2. Login:
   - Username: `Kfupmsdaia`
   - Password: `aerospace`
3. **You should see your session!**
4. Click "View Chat" to see the messages
5. **Test feedback:**
   - Go back to chatbot
   - Click 👍 or 👎 on a message
   - Go to Admin → Feedback tab
   - **Feedback should appear!**

---

## Verification Checklist

✅ Supabase project created
✅ Tables created (check Table Editor in Supabase)
✅ Environment variables added to Vercel
✅ Code deployed to Vercel
✅ Asked a question on chatbot
✅ Admin panel shows the session
✅ After 20min, data still there!

---

## What Changed?

**Before:**
- ❌ All data in `/tmp` (lost every 10 min)
- ❌ Admin panel empty after restart
- ❌ Users lose their chat history

**After:**
- ✅ Chat/feedback in Supabase (persistent cloud DB)
- ✅ Course data in SQLite (still fast for queries)
- ✅ Admin panel works perfectly
- ✅ Zero data loss!

---

## Need Help?

### "Tables not appearing in Supabase"
→ Re-run the SQL from Step 3

### "Error: supabase-py not installed"
→ Make sure `requirements.txt` has `supabase==2.3.0`

### "Admin panel shows no sessions"
→ Check Vercel logs: `vercel logs`
→ Look for: `✓ Using Supabase for chat/feedback`

### "Still losing data"
→ Check Vercel env vars are set correctly
→ Make sure you used `service_role` key, not `anon` key

---

## Cost

**Free tier includes:**
- 500MB database storage
- 1GB file storage
- Unlimited API requests
- 2 GB bandwidth

You'll only hit limits if you get **thousands** of users. Current usage will be ~1-5MB.

---

## Done! 🚀

Your chatbot now has:
- ✅ Persistent storage (no data loss)
- ✅ Working admin panel
- ✅ User session history
- ✅ Feedback tracking
- ✅ Production-ready!

Time to celebrate! 🎉
