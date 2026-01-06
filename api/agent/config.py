# KFUPM Course Advisor Agent Configuration

import os
from pathlib import Path

# === Paths ===
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "SQL"
DB_PATH = DATA_DIR / "kfupm_relational.db"

# === vLLM Configuration ===
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "/home/shared_dir/Qwen3-30B-A3B-Instruct-2507")

# === LLM Parameters ===
# Temperature: 0.1 for SQL generation (very deterministic), 0.4 for formatting
LLM_TEMPERATURE = 0.1  # Low for accurate SQL generation
LLM_MAX_TOKENS = 2048  # Enough for complex queries + response
LLM_TOP_P = 0.95       # Slightly higher for better token selection

# === Agent Settings ===
MAX_SQL_RETRIES = 2    # Retry SQL generation on syntax errors
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
ENABLE_FUZZY_SEARCH = True  # Use FTS5 for fuzzy matching fallback

# === Response Limits ===
MAX_RESULTS_DISPLAY = 50   # Max rows to show in formatted response
MAX_RESULT_CHARS = 8000    # Truncate result JSON for formatting prompt
