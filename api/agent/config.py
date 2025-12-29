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
LLM_TEMPERATURE = 0.3  # Lower for more deterministic SQL generation
LLM_MAX_TOKENS = 2048
LLM_TOP_P = 0.9

# === Agent Settings ===
MAX_SQL_RETRIES = 2  # Retry SQL generation on failure
ENABLE_FUZZY_SEARCH = True  # Use FTS5 for fuzzy matching
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
