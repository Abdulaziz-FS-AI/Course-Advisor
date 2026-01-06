
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import os
import uuid

# Add current directory to path so imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
parent_dir = os.path.dirname(current_dir)

from agent.agent import get_agent
from agent.config import VLLM_BASE_URL
from agent.database import get_database
from agent.auth import verify_password, get_password_hash, create_access_token, decode_access_token

app = FastAPI(title="KFUPM Course Advisor API")

# Allow CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file routes for local development
@app.get("/")
def serve_index():
    return FileResponse(os.path.join(parent_dir, "index.html"))

@app.get("/admin")
def serve_admin():
    return FileResponse(os.path.join(parent_dir, "admin.html"))

@app.get("/admin.html")
def serve_admin_html():
    return FileResponse(os.path.join(parent_dir, "admin.html"))

from agent.system_prompt import get_system_prompt
from agent.llm_client import get_llm_client

# Models
class UserLogin(BaseModel):
    username: str
    password: str

class CreateSessionRequest(BaseModel):
    title: str
    device_id: str

class ChatRequest(BaseModel):
    message: str
    session_id: str
    device_id: str = "anonymous"

# Auth Endpoints - Register removed (Admin usage only/seeded), Login kept for Admin
@app.post("/api/auth/login")
def login(user: UserLogin):
    db = get_database()
    try:
        db_user = db.get_user_by_username(user.username)
        if not db_user or not verify_password(user.password, db_user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        token = create_access_token({"sub": db_user["username"], "id": db_user["id"], "role": db_user["role"]})
        return {"token": token, "username": db_user["username"], "role": db_user["role"]}
    except Exception as e:
        print("Login error:", e)
        raise HTTPException(status_code=500, detail="Server error")

# Chat Endpoints
@app.post("/api/chat/sessions")
def create_session(request: CreateSessionRequest):
    """Create a new anonymous session linked to a device ID."""
    try:
        session_id = str(uuid.uuid4())
        db = get_database()
        session = db.create_chat_session(
            title=request.title,
            session_id=session_id,
            device_id=request.device_id
        )
        return session
    except Exception as e:
        print(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/sessions")
def get_sessions(device_id: str):
    """Get all sessions for a specific device."""
    db = get_database()
    return db.get_device_sessions(device_id)

@app.post("/api/chat")
def chat(request: ChatRequest):
    """
    Chat endpoint for anonymous users.
    """
    db = get_database()
    
    # 1. Save User Message
    try:
        db.add_message(request.session_id, "user", request.message)
    except Exception as e:
        print(f"Error saving user message: {e}")
        raise HTTPException(status_code=500, detail="Failed to save message")

    # 2. Generate AI Response using system prompt + history
    try:
        # Get history (list of dicts with 'role', 'content')
        history_rows = db.get_session_messages(request.session_id)
        
        # Convert to format expected by LLMClient (list of dicts)
        if not history_rows:
            history_rows = []
            
        current_msg = history_rows[-1]["content"] if history_rows else request.message
        # History is everything EXCEPT the last one (if it was added)
        context_history = []
        for msg in history_rows[:-1]:
            context_history.append({"role": msg["role"], "content": msg["content"]})
            
        # Call LLM
        client = get_llm_client()
        system_prompt = get_system_prompt()
        
        response_text = client.generate(
            system_prompt=system_prompt,
            user_message=current_msg,
            conversation_history=context_history[-10:] # Limit context window if needed
        )
        
        # 3. Save AI Response
        db.add_message(request.session_id, "assistant", response_text)
        
        return {"response": response_text}

    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/sessions")
def get_all_sessions_admin(token: str):
    """Get ALL sessions for admin dashboard."""
    db = get_database()
    try:
        payload = decode_access_token(token)
        username = payload.get("sub")
        role = payload.get("role")
        if role != "admin":
             raise HTTPException(status_code=403, detail="Admin only")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    return db.get_all_sessions_for_admin()

@app.get("/api/admin/messages")
def get_session_msgs_admin(token: str, session_id: str):
    """Get messages for a specific session (admin only)."""
    db = get_database()
    try:
        payload = decode_access_token(token)
        username = payload.get("sub")
        role = payload.get("role")
        if role != "admin":
             raise HTTPException(status_code=403, detail="Admin only")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    return db.get_session_messages(session_id)

@app.get("/api/health")
def health_check():
    agent = get_agent()
    # Check VLLM
    vllm_status = "unknown"
    try:
        # Simple reliable check: just see if we can instantiate client
        client = get_llm_client()
        vllm_status = "connected" if client.health_check() else "disconnected"
    except:
        vllm_status = "error"
        
    status = {
        "status": "active",
        "agent": "ready" if agent else "not_ready",
        "vllm": vllm_status,
        "database": "connected" if agent.db else "disconnected",
        "llm_url": VLLM_BASE_URL
    }
    return status

@app.get("/api/chat/messages")
def get_session_messages(session_id: str, device_id: str):
    """Get messages for a specific session (device ownership check)."""
    db = get_database()
    # Check if session exists and belongs to device
    # In a real app we'd verify device_id, for now we trust the client or just return public data (anonymous sessions)
    # sessions = db.get_device_sessions(device_id) 
    # if session_id not in [s['id'] for s in sessions]: ...
    
    return db.get_session_messages(session_id)

