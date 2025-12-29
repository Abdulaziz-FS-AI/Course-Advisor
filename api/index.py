from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import os

# Add current directory to path so imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from agent.agent import get_agent
from agent.config import VLLM_BASE_URL

app = FastAPI(title="KFUPM Course Advisor API")

# Allow CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = None

class ChatResponse(BaseModel):
    response: str
    query_type: str
    sql: Optional[str] = None
    results: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None

@app.get("/api/health")
def health_check():
    agent = get_agent()
    status = {
        "status": "online",
        "database": "connected" if agent.db else "disconnected",
        "llm_url": VLLM_BASE_URL
    }
    return status

@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    agent = get_agent()
    
    # Update history if provided
    if request.history:
        agent.conversation_history = request.history

    response = agent.process_query(request.message)
    
    return ChatResponse(
        response=response.message,
        query_type=response.query_type.value,
        sql=response.sql_used,
        results=response.raw_results,
        error=response.error
    )
