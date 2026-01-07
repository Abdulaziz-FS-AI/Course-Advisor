# Vercel Deployment Guide for KFUPM Course Advisor

## Current Setup Status

✅ **Database**: Included in git (2.3 MB)
✅ **ngrok**: Running at https://precapitalistic-eldora-uninterpolative.ngrok-free.dev
✅ **vLLM**: Exposed via ngrok on port 8000
✅ **Configuration**: `.env.production` configured

## Prerequisites

1. **ngrok must be running** to expose vLLM to Vercel
2. **vLLM server must be running** on localhost:8000
3. **Vercel account** with project created

## Step-by-Step Deployment

### 1. Start Required Services

```bash
# Terminal 1: Start vLLM (if not already running)
python3 -m vllm.entrypoints.openai.api_server \
  --model /home/shared_dir/Qwen3-30B-A3B-Instruct-2507 \
  --host 0.0.0.0 --port 8000 \
  --tensor-parallel-size 4 \
  --max-model-len 8192

# Terminal 2: Start ngrok tunnel
cd /home/shared_dir/vercel_app
./ngrok http 8000
```

### 2. Get ngrok Public URL

Visit: http://localhost:4040

Or run:
```bash
curl -s http://127.0.0.1:4040/api/tunnels | \
  python3 -c "import sys, json; data=json.load(sys.stdin); print([t['public_url'] for t in data.get('tunnels', []) if 'https' in t['public_url']][0])"
```

### 3. Configure Vercel Environment Variables

Go to: https://vercel.com/your-username/your-project/settings/environment-variables

Set these variables:

| Key | Value | Environment |
|-----|-------|------------|
| `VLLM_BASE_URL` | `https://your-ngrok-url.ngrok-free.dev/v1` | Production |
| `MODEL_NAME` | `/home/shared_dir/Qwen3-30B-A3B-Instruct-2507` | Production |
| `DEBUG_MODE` | `false` | Production |

**Current ngrok URL**: `https://precapitalistic-eldora-uninterpolative.ngrok-free.dev/v1`

### 4. Deploy to Vercel

```bash
# Install Vercel CLI (if not installed)
npm i -g vercel

# Deploy
cd /home/shared_dir/vercel_app
vercel --prod
```

Or push to GitHub and Vercel will auto-deploy.

### 5. Verify Deployment

After deployment, test your Vercel URL:

```bash
curl -X POST https://your-app.vercel.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"hi","device_id":"test","session_id":"test"}'
```

## Important Notes

### ⚠️ ngrok Free Tier Limitations

- **Tunnel expires** when ngrok process stops
- **URL changes** each time you restart ngrok (unless you have a paid plan)
- **Solution**: Use ngrok paid plan for stable URLs, or restart tunnel and update Vercel env vars

### Database Handling

The database is:
- ✅ Included in git (2.3 MB)
- ✅ Deployed to Vercel
- ✅ Copied to `/tmp` on Vercel for write operations
- ✅ Read-only in production (safe for serverless)

### Troubleshooting

#### 1. "I'm having trouble processing your request"
**Cause**: vLLM not accessible from Vercel

**Fix**:
```bash
# Check if ngrok is running
curl https://your-ngrok-url.ngrok-free.dev/v1/models

# If not, restart ngrok
./ngrok http 8000
```

#### 2. "Database not found"
**Cause**: Database file not deployed

**Fix**:
```bash
# Ensure database is tracked in git
git add api/data/SQL/kfupm_relational.db
git commit -m "Add database for Vercel deployment"
git push
```

#### 3. ngrok URL changed
**Cause**: ngrok restarted

**Fix**:
1. Get new URL: `curl http://localhost:4040/api/tunnels`
2. Update Vercel env var: `VLLM_BASE_URL`
3. Redeploy Vercel

## Alternative: Self-Hosted Deployment

If ngrok is unstable, consider:

1. **Railway.app**: Deploy vLLM as a service
2. **Modal.com**: Serverless GPU hosting
3. **Replicate.com**: Model hosting
4. **Your own VPS**: With static IP

## Monitoring

Check logs in Vercel dashboard:
https://vercel.com/your-project/deployments

Or via CLI:
```bash
vercel logs your-deployment-url
```

## Auto-Restart ngrok (Optional)

Create a systemd service or cron job to keep ngrok running:

```bash
# Add to crontab
*/5 * * * * pgrep ngrok || cd /home/shared_dir/vercel_app && nohup ./ngrok http 8000 > ngrok.log 2>&1 &
```

## Current Status

Run this to check everything:
```bash
cd /home/shared_dir/vercel_app
echo "vLLM Status:" && curl -s http://localhost:8000/v1/models | head -2
echo "\nngrok Status:" && curl -s http://localhost:4040/api/tunnels | grep -o 'https://[^"]*ngrok[^"]*'
echo "\nDatabase:" && ls -lh api/data/SQL/*.db
```
