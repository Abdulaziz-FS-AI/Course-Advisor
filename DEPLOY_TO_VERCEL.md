# 🚀 Deploying KFUPM Course Advisor to Vercel

## Prerequisites
1. **Vercel CLI**: Install with `npm install -g vercel`
2. **Ngrok**: Download from [ngrok.com](https://ngrok.com)
3. **vLLM Running Locally**: Your GPU machine must be on.

## Step 1: Start System & Tunnel
On your GPU machine (this machine), run:

1. **Start vLLM** (if not running):
   ```bash
   bash /home/shared_dir/start_vllm.sh
   ```

2. **Start Ngrok Tunnel**:
   ```bash
   ngrok http 8000
   ```
   *Copy the Forwarding URL (e.g., `https://xxxx-xx-xx.ngrok-free.app`)*

## Step 2: Deploy to Vercel
1. Go to the deployment folder:
   ```bash
   cd /home/shared_dir/vercel_app
   ```

2. Deploy using Vercel CLI:
   ```bash
   vercel --prod
   ```

3. **Configure Environment Variables**:
   During deployment (or in Vercel Dashboard Settings), set:
   - `VLLM_BASE_URL`: Paste your ngrok URL + `/v1` (e.g., `https://xxxx.ngrok-free.app/v1`)
   - `MODEL_NAME`: `/home/shared_dir/Qwen3-30B-A3B-Instruct-2507` (or whatever the model name is if running elsewhere)

## Step 3: Done!
Your agent is now live on Vercel!
- The frontend talks to `/api/chat`.
- The backend tunnels requests to your local GPU.
