# 🔴 DATABASE PERSISTENCE ISSUE - READ THIS!

## The Problem

Your chat sessions and feedback **ARE being saved locally**, but **NOT on Vercel deployment**.

### Current Status

**Local (✅ WORKING):**
- 26 chat sessions saved
- 85 messages saved
- 2 feedback entries saved
- Database: `/home/shared_dir/Kfupm_Chatbot/api/data/SQL/kfupm_relational.db`

**Vercel (❌ BROKEN):**
- Database copied to `/tmp/kfupm_relational.db` (ephemeral storage)
- **ALL DATA LOST every ~10-15 minutes** when serverless function restarts
- Users see their chats disappear
- Admin panel shows no data

## Why This Happens

Vercel serverless functions use `/tmp` as temporary storage that gets **completely wiped**:
- After ~10-15 minutes of inactivity
- On every new deployment
- When the function cold-starts

**Location in code:** [database.py:26-46](api/agent/database.py#L26-L46)

```python
if is_vercel:
    tmp_path = Path("/tmp") / db_path.name  # ❌ This is ephemeral!
    shutil.copy2(db_path, tmp_path)
    self.db_path = tmp_path  # Data will be lost!
```

## Solutions

### Option 1: Vercel Postgres (Recommended ⭐)

**Pros:**
- Built into Vercel
- Persistent storage
- Scales automatically
- Free tier available

**Steps:**
1. Go to your Vercel project dashboard
2. Click "Storage" → "Create Database" → "Postgres"
3. Install: `pip install psycopg2-binary`
4. Update `database.py` to use PostgreSQL instead of SQLite

**Cost:** Free tier: 256MB storage, 60 compute hours/month

### Option 2: PlanetScale MySQL

**Pros:**
- Free tier
- Serverless MySQL
- Good performance

**Steps:**
1. Sign up at planetscale.com
2. Create database
3. Get connection string
4. Install: `pip install mysql-connector-python`
5. Update `database.py`

### Option 3: Railway.app PostgreSQL

**Pros:**
- Easy setup
- Free $5/month credit
- PostgreSQL

**Steps:**
1. Sign up at railway.app
2. Deploy PostgreSQL
3. Get connection URL
4. Update `database.py`

### Option 4: Turso (SQLite Cloud)

**Pros:**
- Keep using SQLite syntax
- Edge database
- Free tier

**Steps:**
1. Sign up at turso.tech
2. Create database
3. Install: `pip install libsql-client`
4. Update `database.py` to use Turso

## Temporary Fix (Local Development Only)

Run locally and access via ngrok/cloudflare tunnel:

```bash
cd /home/shared_dir/Kfupm_Chatbot
uvicorn api.index:app --reload --port 8080
```

Then use Cloudflare Tunnel or ngrok to expose it publicly.

## Admin Panel Access

**Login Credentials:**
- URL: `https://your-domain.vercel.app/admin`
- Username: `Kfupmsdaia`
- Password: `aerospace`

**If admin shows no data:**
- You're on Vercel → /tmp was wiped → data is gone
- Check server logs in Vercel dashboard for warnings

## What I've Added

✅ Comprehensive logging in database operations:
- [database.py:441](api/agent/database.py#L441) - Message save logging
- [database.py:360](api/agent/database.py#L360) - Session creation logging
- [database.py:501](api/agent/database.py#L501) - Feedback save logging

✅ Warning messages when using /tmp:
- [database.py:43-45](api/agent/database.py#L43-L45)

## Next Steps

1. **Choose a persistent database** (I recommend Vercel Postgres)
2. **Migrate your schema** to the new database
3. **Update database.py** to connect to persistent storage
4. **Test on Vercel** to confirm persistence

## Need Help?

Check Vercel logs:
```bash
vercel logs <your-deployment-url>
```

Look for these warning messages:
```
⚠️ WARNING: Database is in /tmp (ephemeral storage)!
⚠️ Data will be LOST on function restart!
```

---

**Summary:** Your code is perfect, but you need a persistent database instead of SQLite in /tmp on Vercel!
