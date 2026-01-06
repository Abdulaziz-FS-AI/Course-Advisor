
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

# Models
class UserLogin(BaseModel):
    username: str
    password: str

class GuestLogin(BaseModel):
    username: str

class UserRegister(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    message: str
    username: Optional[str] = None
    token: Optional[str] = None
    session_id: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = None

class ChatResponse(BaseModel):
    response: str
    query_type: str
    session_id: str
    sql: Optional[str] = None
    results: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None

class HistoryResponse(BaseModel):
    sessions: List[Dict[str, Any]]

# Auth Endpoints
@app.post("/api/auth/register")
def register(user: UserRegister):
    db = get_database()
    try:
        hashed_pw = get_password_hash(user.password)
        new_user = db.create_user(user.username, hashed_pw)
        return {"message": "User registered successfully", "user_id": new_user["id"]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

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


@app.post("/api/auth/guest")
def guest_login(user: GuestLogin):
    """Guest login – only a username is required.
    - If the username already exists (and is not admin) return an error indicating the name is taken.
    - If the username does not exist, create a new guest user with a dummy password hash.
    """
    db = get_database()
    username = user.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="Username required")

    # Check for existing user
    db_user = db.get_user_by_username(username)
    if db_user:
        if db_user["role"] == "admin":
            raise HTTPException(status_code=403, detail="Admins must use password login")
        else:
            raise HTTPException(status_code=400, detail="Name already taken. Choose another.")

    # Create new guest user with a short dummy password (bcrypt limit 72 bytes)
    dummy_password = "guest_user_no_password"[:72]
    dummy_hash = get_password_hash(dummy_password)
    new_user = db.create_user(username, dummy_hash, role='user')
    token = create_access_token({"sub": new_user["username"], "id": new_user["id"], "role": "user"})
    return {"token": token, "username": new_user["username"], "role": "user"}


@app.get("/api/health")
def health_check():
    agent = get_agent()
    status = {
        "status": "online",
        "database": "connected" if agent.db else "disconnected",
        "llm_url": VLLM_BASE_URL
    }
    return status

@app.get("/api/history")
def get_history(token: str):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    db = get_database()
    sessions = db.get_user_sessions(payload["id"])
    return {"sessions": sessions}

@app.get("/api/chats/{session_id}")
def get_chat_details(session_id: str, token: str):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    db = get_database()
    messages = db.get_session_messages(session_id)
    return {"messages": messages}

@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    agent = get_agent()
    db = get_database()
    
    session_id = request.session_id
    user_id = None
    
    # Authenticate if token provided
    if request.token:
        payload = decode_access_token(request.token)
        if payload:
            user_id = payload["id"]
    
    # Create session if needed
    if not session_id and user_id:
        session_id = str(uuid.uuid4())
        # Use first few chars of message as title
        title = request.message[:30] + "..." if len(request.message) > 30 else request.message
        db.create_chat_session(user_id, title, session_id)
    
    # Save User Message
    if session_id and user_id:
        db.add_message(session_id, "user", request.message)

    # Process Query
    response = agent.process_query(request.message)
    
    # Save Assistant Message
    if session_id and user_id:
        # Convert response to string if needed, or structured
        content = response.message
        db.add_message(session_id, "assistant", content)
    
    return ChatResponse(
        response=response.message,
        query_type=response.query_type.value,
        session_id=session_id or "anonymous",
        sql=response.sql_used,
        results=response.raw_results,
        error=response.error
    )

# Admin Endpoints
@app.get("/api/admin/users")
def get_all_users(token: str):
    payload = decode_access_token(token)
    if not payload or payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    db = get_database()
    users = db.get_all_users()
    return {"users": users}

@app.get("/api/admin/users/{user_id}/chats")
def get_user_chats_admin(user_id: int, token: str):
    payload = decode_access_token(token)
    if not payload or payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    db = get_database()
    sessions = db.get_user_sessions(user_id)
    return {"sessions": sessions}

@app.get("/api/admin/chats/{session_id}")
def get_chat_details_admin(session_id: str, token: str):
    payload = decode_access_token(token)
    if not payload or payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    db = get_database()
    messages = db.get_session_messages(session_id)
    return {"messages": messages}
