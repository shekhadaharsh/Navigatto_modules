import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database.db import Base

class ChatSession(Base):
    """
    Represents a chatbot session (conversation thread).
    """
    __tablename__ = "chat_sessions"
    __table_args__ = {"schema": "dbo"}

    session_id = Column(String(100), primary_key=True)
    title      = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Cascading delete so messages are cleaned up when session is deleted
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    """
    Represents an individual chat message (either from 'user' or 'assistant').
    """
    __tablename__ = "chat_messages"
    __table_args__ = {"schema": "dbo"}

    id          = Column(Integer, primary_key=True, autoincrement=True)
    session_id  = Column(String(100), ForeignKey("dbo.chat_sessions.session_id", ondelete="CASCADE"), nullable=False)
    role        = Column(String(50), nullable=False)  # 'user' or 'assistant'
    content     = Column(Text, nullable=False)
    sql         = Column(Text, nullable=True)
    columns     = Column(Text, nullable=True)         # JSON-serialized list of strings
    rows        = Column(Text, nullable=True)            # JSON-serialized list of lists
    suggestions = Column(Text, nullable=True)         # JSON-serialized list of strings
    status      = Column(String(50), nullable=True)   # 'success', 'error', 'out_of_scope', etc.
    timestamp   = Column(DateTime, default=datetime.datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")
