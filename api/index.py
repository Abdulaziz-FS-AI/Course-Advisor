
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

class FeedbackRequest(BaseModel):
    session_id: str
    message_id: int
    rating: str  # 'up' or 'down'
    device_id: str
    comment: Optional[str] = None

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
    # Validate required fields
    if not request.session_id:
        raise HTTPException(status_code=422, detail="session_id is required")
    if not request.message:
        raise HTTPException(status_code=422, detail="message is required")
    
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
        # Call Agent
        # Prepare context by converting history rows to simple dicts
        context_history = []
        if history_rows:
            # History is all previous messages. Current message was just added.
            # We want context to be previous messages.
            # Actually, `add_message` added the USER message at the end.
            # So history_rows[-1] is the current message.
            # We want to pass previous history to the agent.
            for msg in history_rows[:-1]: 
                context_history.append({"role": msg["role"], "content": msg["content"]})
        
        agent = get_agent()
        agent_response = agent.process_query(request.message, context_history)
        
        response_text = agent_response.message

        # 3. Save AI Response and get message ID
        assistant_msg = db.add_message(request.session_id, "assistant", response_text)

        return {
            "response": response_text,
            "message_id": assistant_msg.get("message_id")
        }

    except Exception as e:
        print(f"Chat error: {e}")
        # In case of error, try to return a friendly message
        return {"response": "I encountered an error connecting to my brain. Please try again."}


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

@app.post("/api/feedback")
def submit_feedback(request: FeedbackRequest):
    """Submit feedback for a message."""
    db = get_database()

    # Validate rating
    if request.rating not in ['up', 'down']:
        raise HTTPException(status_code=400, detail="Rating must be 'up' or 'down'")

    try:
        # Get or create anonymous user
        anon_user = db.get_user_by_username("anonymous_user")
        if not anon_user:
            db.create_user("anonymous_user", "nopassword", role="user")
            anon_user = db.get_user_by_username("anonymous_user")

        user_id = anon_user["id"]

        # Create feedback
        feedback = db.create_feedback(
            user_id=user_id,
            session_id=request.session_id,
            message_id=request.message_id,
            rating=request.rating,
            comment=request.comment
        )

        return {"status": "success", "feedback": feedback}
    except Exception as e:
        print(f"Feedback error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save feedback")

@app.get("/api/admin/feedback")
def get_all_feedback_admin(token: str):
    """Get all feedback for admin dashboard."""
    db = get_database()
    try:
        payload = decode_access_token(token)
        role = payload.get("role")
        if role != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

    return db.get_all_feedback()

