from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List
import uuid
import traceback

from app.database import get_db
from app.models import ChatSession, Message
from app.services.llm_service import LLMService
from app.services.faq_service import FAQService
from app.services.escalation import EscalationService

router = APIRouter(prefix="/chat", tags=["chat"])

llm_service = LLMService()
faq_service = FAQService()
escalation_service = EscalationService()

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    session_id: str
    response: str
    faq_matched: bool
    confidence: Optional[int] = None
    escalated: bool = False
    escalation_info: Optional[dict] = None

@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """Main chat endpoint"""
    
    try:
        # Verify session exists
        result = await db.execute(
            select(ChatSession).where(ChatSession.session_id == request.session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if not session.is_active:
            raise HTTPException(status_code=400, detail="Session is closed")
        
        # Check if already escalated
        if session.escalated:
            return ChatResponse(
                session_id=request.session_id,
                response="This conversation has been escalated to human support. A representative will contact you shortly.",
                faq_matched=False,
                escalated=True,
                escalation_info=escalation_service.get_escalation_status(request.session_id)
            )
        
        # Save user message
        user_msg = Message(
            session_id=request.session_id,
            role="user",
            content=request.message
        )
        db.add(user_msg)
        await db.commit()
        
        # Get conversation history
        history_result = await db.execute(
            select(Message)
            .where(Message.session_id == request.session_id)
            .order_by(Message.timestamp)
        )
        all_messages = history_result.scalars().all()
        
        # Convert to format for LLM (exclude the just-added user message)
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in all_messages[:-1]  # Exclude last message (just added)
        ]
        
        # Try FAQ matching first
        faq_match = faq_service.find_matching_faq(request.message)
        
        if faq_match and faq_match.get('confidence', 0) > 80:
            response_text = faq_match['answer']
            faq_matched = True
            confidence = faq_match['confidence']
        else:
            # Generate response using LLM with FAQ context
            faq_context = faq_service.get_faq_context()
            response_text = await llm_service.generate_response(
                request.message,
                conversation_history,
                faq_context
            )
            faq_matched = False
            confidence = None
        
        # Save assistant response
        assistant_msg = Message(
            session_id=request.session_id,
            role="assistant",
            content=response_text,
            faq_matched=faq_matched,
            confidence_score=confidence
        )
        db.add(assistant_msg)
        
        # Check for escalation need
        user_message_count = sum(1 for msg in all_messages if msg.role == "user")
        escalation_check = await llm_service.detect_escalation_need(
            request.message,
            user_message_count
        )
        
        escalation_info = None
        if escalation_check.get('needs_escalation'):
            # Summarize conversation
            summary = await llm_service.summarize_conversation(conversation_history)
            
            # Escalate
            escalation_info = escalation_service.escalate_session(
                request.session_id,
                escalation_check.get('reason', 'User request'),
                summary,
                [{"content": msg.content, "role": msg.role} for msg in all_messages]
            )
            
            # Update session
            session.escalated = True
            session.escalation_reason = escalation_check.get('reason')
            
            response_text += "\n\nI've escalated your query to our human support team who can better assist you. Your ticket ID is: " + escalation_info['ticket_id']
        
        await db.commit()
        
        return ChatResponse(
            session_id=request.session_id,
            response=response_text,
            faq_matched=faq_matched,
            confidence=confidence,
            escalated=escalation_check.get('needs_escalation', False),
            escalation_info=escalation_info
        )
    
    except HTTPException:
        raise
    except Exception as e:
        # Log the full error for debugging
        print(f"Error in chat endpoint: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your message: {str(e)}"
        )

@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve chat history for a session"""
    
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.timestamp)
    )
    messages = result.scalars().all()
    
    return {
        "session_id": session_id,
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "faq_matched": msg.faq_matched
            }
            for msg in messages
        ]
    }
