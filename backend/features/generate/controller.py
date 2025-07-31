"""
Meme generation controller handling AI-powered meme creation endpoints.

This module provides the HTTP interface for the meme generation system,
streaming AI responses in real-time to provide immediate user feedback.
The streaming approach enhances user experience by showing progress
during the multi-step generation process.
"""
import logging
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from database.core import get_session
from features.auth.service import get_current_user
from entities.user import User
from .models import GenerateMemeRequest
from .service import generate_meme_stream

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/generate", tags=["generate"])


@router.post(
    "/meme",
    summary="Generate a meme using AI",
)
def generate_meme(
    request: GenerateMemeRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """
    Stream AI-generated meme creation in real-time.
    
    Processes user prompts through a multi-agent workflow that:
    1. Analyzes the request to determine meme style
    2. Generates appropriate captions and context
    3. Creates the final meme image with text overlay
    4. Stores the result for user access
    
    The streaming response uses Server-Sent Events (SSE) to push
    updates as the AI agents work, providing transparency into
    the generation process.
    
    Args:
        request: Contains prompt, conversation ID, and model selection
        session: Database session for persistence operations
        current_user: Authenticated user making the request
        
    Returns:
        StreamingResponse: SSE stream with generation updates and final result
        
    Note:
        Frontend should handle SSE parsing to display progress messages
        and render the final meme image when complete.
    """
    logger.info(f"Generating meme for user {current_user.id}")
    
    # Delegate to service layer for business logic and streaming
    return generate_meme_stream(
        prompt=request.prompt,
        conversation_id=request.conversation_id,
        manager_model=request.manager_model,
        session=session,
        current_user=current_user,
    )