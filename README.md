# KFUPM Course Advisor

AI-powered course advisor system for King Fahd University of Petroleum & Minerals.

## Features

- Natural language queries for courses, departments, and degree plans
- Text-to-SQL conversion using LLM (Qwen3-30B)
- Anonymous session tracking
- Admin dashboard with feedback analytics
- 11MB SQLite database with comprehensive KFUPM academic data

## Stack

- **Backend**: FastAPI + Python
- **AI**: vLLM-served Qwen3-30B model
- **Database**: SQLite (3994 courses, 2130 program plans, 43 concentrations)
- **Deployment**: Vercel

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.production.example .env.local
# Edit .env.local with your vLLM endpoint

# Run locally
uvicorn api.index:app --reload

# Access at http://localhost:8000
```

## Deployment

Deployed on Vercel. Environment variables required:
- `VLLM_BASE_URL` - vLLM server endpoint
- `MODEL_NAME` - Path to Qwen model
- `SECRET_KEY` - JWT secret

## Project Structure

```
api/
  ├── index.py           # FastAPI app
  ├── agent/
  │   ├── agent.py       # Main agent logic
  │   ├── system_prompt.py  # Prompt engineering
  │   ├── database.py    # Database manager
  │   ├── llm_client.py  # vLLM client
  │   └── config.py      # Configuration
  ├── data/SQL/
  │   └── kfupm_relational.db  # SQLite database
index.html             # Main UI
admin.html             # Admin dashboard
```

## License

Academic use only.
