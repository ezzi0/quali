"""
Agent endpoint with SSE streaming

Implements OpenAI Agent SDK patterns:
- Single-agent system with tools and guardrails
- Structured outputs (LeadQualification)
- Session memory
- Human-in-the-loop triggers
- Relevance and safety guardrails
"""
import json
import asyncio
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..config import get_settings
from ..deps import get_db, get_redis
from ..auth import verify_optional_secret
from ..logging import get_logger
from ..services.agent import QualificationAgent, AgentContext
from ..services.session_store import SessionStore

settings = get_settings()
logger = get_logger(__name__)

router = APIRouter()


class AgentTurnRequest(BaseModel):
    """Request for agent turn"""
    message: str
    lead_id: int | None = None
    session_id: str | None = None
    context: Dict[str, Any] | None = None


@router.post("/turn")
async def agent_turn(
    request: AgentTurnRequest,
    db: Session = Depends(get_db),
    redis = Depends(get_redis),
    _auth: None = Depends(verify_optional_secret),
):
    """
    Process agent turn with proper Agent SDK patterns.

    Features:
    - Guardrails (relevance, safety)
    - Session memory (persisted in Redis)
    - Tool execution with limits
    - Human-in-the-loop triggers
    - Structured output
    - Session recovery by email/phone
    """

    # Initialize agent and session store
    agent = QualificationAgent(db)
    session_store = SessionStore(redis)

    # Load or create context
    if request.context:
        context = AgentContext(**request.context)
    else:
        # Try to load from Redis
        if request.session_id:
            stored_context = session_store.get_session(request.session_id)
            if stored_context:
                context = AgentContext(**stored_context)
                logger.info("session_resumed", session_id=request.session_id)
            else:
                context = AgentContext(
                    lead_id=request.lead_id,
                    session_id=request.session_id
                )
        else:
            context = AgentContext(
                lead_id=request.lead_id,
                session_id=request.session_id
            )

    async def generate():
        """Generate SSE stream"""
        try:
            # Run agent
            result = await agent.run(request.message, context)

            # Stream messages
            for msg in result["messages"]:
                if msg.get("type") == "tool_call":
                    # Tool call event
                    yield f"data: {json.dumps({'type': 'tool_start', 'tool': msg['tool']})}\n\n"
                    yield f"data: {json.dumps({'type': 'tool_result', 'tool': msg['tool'], 'result': msg['result']})}\n\n"

                elif msg.get("type") == "text":
                    # Assistant message - stream as complete message for faster response
                    content = msg["content"] or ""
                    yield f"data: {json.dumps({'type': 'text', 'content': content})}\n\n"

            # Save session to Redis
            if context.session_id:
                # Extract email/phone if available
                contact_info = session_store.extract_contact_from_context(result['context'].dict())
                session_store.save_session(
                    context.session_id,
                    result['context'].dict(),
                    email=contact_info.get('email'),
                    phone=contact_info.get('phone')
                )
            
            # Send context update
            yield f"data: {json.dumps({'type': 'context_update', 'context': result['context'].dict()})}\n\n"

            # Check if we should escalate to human
            if result.get("escalate_to_human"):
                yield f"data: {json.dumps({'type': 'escalate', 'reason': 'max_attempts'})}\n\n"

            # Check if qualification is complete
            if not result["should_continue"]:
                yield f"data: {json.dumps({'type': 'complete', 'qualification': result.get('qualification')})}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error("agent_turn_failed", error=str(e), exc_info=True)
            # Include error details for debugging (remove in production)
            error_msg = f"Error: {str(e)}" if settings.environment == "development" else "An error occurred. Please try again or speak with a specialist."
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/session")
async def create_session(
    lead_id: int | None = None,
    email: str | None = None,
    phone: str | None = None,
    session_id: str | None = None,
    redis = Depends(get_redis),
    _auth: None = Depends(verify_optional_secret),
):
    """
    Create or recover a chat session
    
    - If email/phone provided, tries to recover previous session
    - Otherwise creates new session
    """
    import uuid
    
    session_store = SessionStore(redis)
    session_store = SessionStore(redis)

    # Try to resume explicit session_id first
    if session_id:
        existing_context = session_store.get_session(session_id)
        if existing_context:
            logger.info("session_recovered_by_id", session_id=session_id)
            return {
                "session_id": session_id,
                "lead_id": existing_context.get("lead_id"),
                "context": existing_context,
                "resumed": True
            }

    # Try to recover session by email or phone
    if email:
        existing_context = session_store.get_session_by_email(email)
        if existing_context:
            logger.info("session_recovered_by_email", email=email)
            return {
                "session_id": existing_context.get("session_id"),
                "lead_id": existing_context.get("lead_id"),
                "context": existing_context,
                "resumed": True
            }
    
    if phone:
        existing_context = session_store.get_session_by_phone(phone)
        if existing_context:
            logger.info("session_recovered_by_phone", phone=phone)
            return {
                "session_id": existing_context.get("session_id"),
                "lead_id": existing_context.get("lead_id"),
                "context": existing_context,
                "resumed": True
            }
    
    # Create new session
    session_id = str(uuid.uuid4())
    context = AgentContext(
        lead_id=lead_id,
        session_id=session_id
    )
    
    # Save to Redis
    session_store.save_session(session_id, context.dict())

    return {
        "session_id": session_id,
        "lead_id": lead_id,
        "context": context.dict(),
        "resumed": False
    }
