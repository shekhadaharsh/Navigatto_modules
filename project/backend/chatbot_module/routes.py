"""
routes.py — FastAPI endpoints for the Text-to-SQL Chatbot.
Exposes:
  - POST /api/chatbot/chat
  - GET /api/chatbot/health
"""

import os
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from chatbot_module import pipeline
from chatbot_module import db_executor
from chatbot_module import schema_service

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []


@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Main API endpoint for the chatbot.
    Receives user query and history, processes it through the pipeline.
    """
    # Verify that the Groq API key is present
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    if not groq_key:
        raise HTTPException(
            status_code=500,
            detail="Chatbot is not configured: GROQ_API_KEY environment variable is missing."
        )

    try:
        # Convert Pydantic models to dicts for the pipeline
        history_list = []
        if request.history:
            history_list = [msg.model_dump() for msg in request.history]

        result = await pipeline.process_query(request.message, history=history_list)
        return result
    except Exception as e:
        print(f"[ChatbotRouter] Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
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
