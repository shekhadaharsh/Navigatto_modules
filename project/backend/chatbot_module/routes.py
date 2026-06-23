"""
routes.py — FastAPI endpoints for the Text-to-SQL Chatbot with persistent session storage.
Exposes:
  - POST /api/chatbot/chat
  - POST /api/chatbot/sessions
  - GET /api/chatbot/sessions
  - GET /api/chatbot/sessions/{session_id}
  - DELETE /api/chatbot/sessions/{session_id}
  - GET /api/chatbot/health
"""

import os
import uuid
import json
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.db import get_db
from chatbot_module import pipeline
from chatbot_module import db_executor
from chatbot_module import schema_service
from chatbot_module.model import ChatSession, ChatMessage as DB_ChatMessage

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


@router.post("/sessions")
def create_session(db: Session = Depends(get_db)):
    """Creates a new chatbot session."""
    session_id = str(uuid.uuid4())
    new_session = ChatSession(session_id=session_id, title="New Chat")
    db.add(new_session)
    db.commit()
    return {"session_id": session_id, "title": new_session.title}


@router.get("/sessions")
def get_sessions(db: Session = Depends(get_db)):
    """Retrieves all chat sessions ordered by created time descending."""
    sessions = db.query(ChatSession).order_by(ChatSession.created_at.desc()).all()
    return [
        {
            "session_id": s.session_id, 
            "title": s.title or "New Chat", 
            "created_at": s.created_at.isoformat()
        } 
        for s in sessions
    ]


@router.get("/sessions/{session_id}")
def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    """Retrieves all messages for a given chat session formatted for UI."""
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = db.query(DB_ChatMessage).filter(DB_ChatMessage.session_id == session_id).order_by(DB_ChatMessage.timestamp.asc()).all()
    
    formatted_messages = []
    for msg in messages:
        # Safely load JSON fields
        columns_val = json.loads(msg.columns) if msg.columns else []
        rows_val = json.loads(msg.rows) if msg.rows else []
        suggestions_val = json.loads(msg.suggestions) if msg.suggestions else []
        
        formatted_messages.append({
            "id": msg.id,
            "sender": "bot" if msg.role == "assistant" else "user",
            "text": msg.content,
            "sql": msg.sql,
            "columns": columns_val,
            "rows": rows_val,
            "suggestions": suggestions_val,
            "status": msg.status,
            "timestamp": msg.timestamp.strftime("%I:%M %p")
        })
    return formatted_messages


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db)):
    """Deletes a chat session and its cascading messages."""
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
    return {"success": True, "session_id": session_id}


@router.post("/chat")
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Main API endpoint for the chatbot.
    Receives user query, retrieves session history, runs the text-to-SQL pipeline,
    and stores messages/results in the database.
    """
    # Verify that the Groq API key is present
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    if not groq_key:
        raise HTTPException(
            status_code=500,
            detail="Chatbot is not configured: GROQ_API_KEY environment variable is missing."
        )

    # Resolve or create session ID
    session_id = request.session_id
    is_new_session = False
    
    if not session_id:
        session_id = str(uuid.uuid4())
        is_new_session = True
        new_session = ChatSession(session_id=session_id, title="New Chat")
        db.add(new_session)
        db.commit()
    else:
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session:
            is_new_session = True
            new_session = ChatSession(session_id=session_id, title="New Chat")
            db.add(new_session)
            db.commit()
        else:
            # Check if there are any existing messages
            msg_count = db.query(DB_ChatMessage).filter(DB_ChatMessage.session_id == session_id).count()
            if msg_count == 0:
                is_new_session = True

    try:
        # 1. Fetch history from DB (limit to last 6 messages for context)
        past_messages = db.query(DB_ChatMessage).filter(
            DB_ChatMessage.session_id == session_id
        ).order_by(DB_ChatMessage.timestamp.asc()).all()
        
        history_list = [
            {"role": msg.role, "content": msg.content}
            for msg in past_messages[-6:]
        ]

        # 2. Save user message to database
        user_db_msg = DB_ChatMessage(
            session_id=session_id,
            role="user",
            content=request.message
        )
        db.add(user_db_msg)
        db.commit()

        # Update session title from first message
        if is_new_session:
            session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
            if session:
                title_text = request.message.strip()
                if len(title_text) > 40:
                    title_text = title_text[:37] + "..."
                session.title = title_text
                db.commit()

        # 3. Process query through text-to-sql pipeline
        result = await pipeline.process_query(request.message, history=history_list)

        # 4. Save assistant response to database
        bot_db_msg = DB_ChatMessage(
            session_id=session_id,
            role="assistant",
            content=result.get("message", ""),
            sql=result.get("sql"),
            columns=json.dumps(result.get("columns", [])),
            rows=json.dumps(result.get("rows", [])),
            suggestions=json.dumps(result.get("suggestions", [])),
            status=result.get("status", "success")
        )
        db.add(bot_db_msg)
        db.commit()

        # Add session_id to response
        result["session_id"] = session_id
        return result

    except Exception as e:
        print(f"[ChatbotRouter] Error in chat endpoint: {e}")
        # Log failure response
        try:
            error_msg = f"Sorry, I encountered an internal error: {str(e)}"
            bot_db_msg = DB_ChatMessage(
                session_id=session_id,
                role="assistant",
                content=error_msg,
                status="error"
            )
            db.add(bot_db_msg)
            db.commit()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")



@router.get("/health")
def health_endpoint():
    """
    Health check endpoint for chatbot dependencies (DB and Schema).
    """
    # Check Schema status
    try:
        schema_info = schema_service.get_schema_summary()
        schema_status = "ok"
    except Exception as e:
        schema_info = {"error": str(e)}
        schema_status = "error"

    # Check DB status
    db_status = db_executor.test_connection()

    # Check LLM status (Verify API key format/presence)
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    llm_status = "ok" if groq_key else "missing_api_key"

    overall_status = "ok" if (schema_status == "ok" and db_status.get("status") == "ok" and llm_status == "ok") else "degraded"

    return {
        "status": overall_status,
        "llm": {
            "status": llm_status,
            "model": os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
        },
        "db": db_status,
        "schema": {
            "status": schema_status,
            **schema_info
        }
    }
