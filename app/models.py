from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

class ChatSession(Base):
    __tablename__ = "chat_session"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime,default=datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
    escalated = Column(Boolean,default=False)
    escalation_reason = Column(Text, nullable=True)

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    role = Column(String) # 'user' or 'assistant'
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.now(timezone.utc))
    faq_matched = Column(Boolean, default=False)
    confidence_score = Column(Integer, nullable=True)

    
