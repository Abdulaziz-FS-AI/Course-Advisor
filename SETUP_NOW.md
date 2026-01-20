# ⚡ Setup Right Now (10 minutes)

You have: ✅ Supabase token
You need: 📍 Supabase project URL

---

## Step 1: Get Your Project URL (2 min)

1. Go to https://supabase.com/dashboard
2. **If you don't have a project yet:**
   - Click "New Project"
   - Name: `kfupm-chatbot`
   - Generate a password (save it!)
   - Region: Singapore or closest
   - Click "Create new project"
   - Wait ~2 minutes

3. **Get your Project URL:**
   - Click Settings (⚙️) → API
   - Copy the **Project URL**: `https://xxxxx.supabase.co`

---

## Step 2: Create Tables (2 min)

1. In Supabase dashboard, click **"SQL Editor"** (left sidebar)
2. Click **"+ New query"**
3. Open the file: `supabase_schema.sql` (in this folder)
4. **Copy ALL the SQL** from that file
5. **Paste** into Supabase SQL Editor
6. Click **"Run"**
7. Should see: Success! 4 tables created ✅

---

## Step 3: Add to Vercel (2 min)

1. Go to https://vercel.com/dashboard
2. Select your KFUPM chatbot project
3. Click **Settings** → **Environment Variables**
4. Add **TWO** variables:

   **Variable 1:**
   ```
   Name: SUPABASE_URL
   Value: https://xxxxx.supabase.co  (from Step 1)
   ```

   **Variable 2:**
   ```
   Name: SUPABASE_KEY
   Value: sbp_b74a04aad24733636a381220a61d8c652889259b
   ```

5. Click **Save** after each

---

## Step 4: Switch to Hybrid Database (1 min)

Run these commands:

```bash
cd /home/shared_dir/Kfupm_Chatbot/api/agent
mv database.py database_sqlite_only.py
mv database_hybrid.py database.py
```

---

## Step 5: Deploy (2 min)

```bash
cd /home/shared_dir/Kfupm_Chatbot
git add .
git commit -m "Switch to Supabase for persistent storage"
git push
```

Wait ~1-2 minutes for Vercel to deploy.

---

## Step 6: Test! (2 min)

1. Go to your chatbot URL
2. Ask a question
3. Go to Supabase → Table Editor → `chat_sessions`
4. **You should see your session!** 🎉

**Admin Panel:**
5. Go to `your-url.vercel.app/admin`
6. Login: `Kfupmsdaia` / `aerospace`
7. **See your sessions!**

---

## ✅ Done!

Your chatbot now has:
- ✅ Persistent storage (no data loss)
- ✅ Working admin panel
- ✅ Cloud database (Supabase)
- ✅ Production ready!

---

## Need Your Project URL?

If you're not sure what your Supabase URL is:

1. Go to https://supabase.com/dashboard
2. Click on your project
3. Settings (⚙️) → API
4. Copy the **Project URL**

It looks like: `https://abcdefghij.supabase.co`

---

## Troubleshooting

**"No tables in Supabase"**
→ Re-run the SQL from `supabase_schema.sql`

**"Still losing data"**
→ Check Vercel environment variables are set
→ Check you're using the hybrid database.py

**"Admin shows no data"**
→ Check Vercel logs: `vercel logs`
→ Look for: "✓ Using Supabase for chat/feedback"

---

Total time: **10 minutes** to fix everything! 🚀
