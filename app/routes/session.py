from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

from app.database import get_db
from app.models import ChatSession, Message

router = APIRouter(prefix="/session", tags=["session"])

class SessionResponse(BaseModel):
    session_id: str
    created_at: str
    is_active: bool
    escalated: bool
    message_count: int

@router.post("/new", response_model=SessionResponse)
async def create_session(db: AsyncSession = Depends(get_db)):
    """Create a new chat session"""
    
    session_id = str(uuid.uuid4())
    
    new_session = ChatSession(
        session_id=session_id,
        is_active=True,
        escalated=False
    )
    
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    
    return SessionResponse(
        session_id=session_id,
        created_at=new_session.created_at.isoformat(),
        is_active=True,
        escalated=False,
        message_count=0
    )

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get session details"""
    
    result = await db.execute(
        select(ChatSession).where(ChatSession.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Count messages
    msg_result = await db.execute(
        select(Message).where(Message.session_id == session_id)
    )
    message_count = len(msg_result.scalars().all())
    
    return SessionResponse(
        session_id=session.session_id,
        created_at=session.created_at.isoformat(),
        is_active=session.is_active,
        escalated=session.escalated,
        message_count=message_count
    )

@router.delete("/{session_id}")
async def close_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Close a chat session"""
    
    result = await db.execute(
        select(ChatSession).where(ChatSession.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.is_active = False
    await db.commit()
    
    return {"message": "Session closed successfully", "session_id": session_id}
