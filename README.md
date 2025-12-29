# KFUPM Course Advisor

AI-powered course advisor for King Fahd University of Petroleum & Minerals.

## Features
- Natural language course search
- Degree plan viewing
- Department information
- Concentration details

## Tech Stack
- FastAPI backend
- SQLite database
- Qwen 30B LLM (via vLLM)
- Vercel deployment

## Environment Variables
Set these in Vercel:
- `VLLM_BASE_URL` - Your vLLM endpoint URL
- `MODEL_NAME` - Model identifier
