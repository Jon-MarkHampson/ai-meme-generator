"""
Message controller handling conversation history and chat message endpoints.

This module provides HTTP endpoints for managing message data within conversations,
bridging the complex Pydantic AI message format with simple chat interfaces.
It handles both message persistence after AI generation and retrieval for
conversation history display.

Key features:
- Conversation message history retrieval with format transformation
- Message persistence after AI generation completion
- Ownership-based access control for message privacy
- Complex-to-simple message format conversion for frontend consumption
- RESTful API design with proper error handling

Technical context:
The system stores messages in Pydantic AI's sophisticated format to preserve
all metadata and context, but transforms them into simple chat messages for
frontend display. This allows full AI framework capabilities while maintaining
a clean user interface.

Security considerations:
- All endpoints require authenticated users
- Message access is limited to conversation owners
- Ownership validation prevents cross-user data access
- Proper HTTP status codes provide clear API responses
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from database.core import get_session
from features.auth.service import get_current_user
from entities.user import User
from .models import MessageCreate, MessageRead, ChatMessage
from .service import (
    list_messages_by_conversation,
    create_message,
    convert_messages_to_chat_format,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/messages", tags=["messages"])


@router.get(
    "/conversations/{conversation_id}",
    response_model=List[ChatMessage],
    summary="List all messages in a conversation",
)
def read_messages(
    conversation_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[ChatMessage]:
    """
    Retrieve all messages from a conversation in chat-friendly format.
    
    This endpoint fetches conversation history and transforms the complex
    Pydantic AI message format into simple chat messages suitable for
    frontend display. Used when loading conversation history or resuming
    previous chat sessions.
    
    Args:
        conversation_id: Unique identifier of the conversation to retrieve messages from
        session: Database session from dependency injection
        current_user: Authenticated user from JWT token validation
        
    Returns:
        List[ChatMessage]: Messages in simple role/content/timestamp format
        
    Data transformation:
        - Complex Pydantic AI message structures are flattened
        - User prompts and AI responses are separated by role
        - Timestamps are preserved for chronological display
        - Metadata is simplified for frontend consumption
        
    Security note:
        Only returns messages from conversations owned by the authenticated
        user, preventing access to other users' private chat history.
        
    Usage context:
        Called when displaying conversation history in chat interfaces
        or when resuming previous generation sessions.
    """
    messages = list_messages_by_conversation(session, conversation_id, current_user.id)
    return convert_messages_to_chat_format(messages)


@router.post(
    "/",
    response_model=MessageRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new message",
)
def create_message_route(
    message_data: MessageCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> MessageRead:
    """
    Persist a complete conversation exchange after AI generation.
    
    This endpoint is called after streaming meme generation completes to
    store the entire conversation exchange (user prompt + AI response) in
    the database. The message is stored in raw Pydantic AI format to
    preserve all context and metadata.
    
    Args:
        message_data: Message creation payload containing Pydantic AI message list
        session: Database session for persistence operations
        current_user: Authenticated user from JWT token validation
        
    Returns:
        MessageRead: Created message record with generated ID and timestamp
        
    Raises:
        HTTPException: 404 if conversation not found or not owned by user
        HTTPException: 422 if message data format is invalid
        
    Technical details:
        - Stores complete Pydantic AI message format for future context
        - Validates conversation ownership before allowing message creation
        - Enables conversation history reconstruction for continued interactions
        
    Usage context:
        Typically called by the generation system after successful meme
        creation to maintain conversation history and context.
        
    Data preservation:
        The raw AI format preserves all metadata needed for future
        context-aware generation requests in the same conversation.
    """
    message = create_message(
        session,
        message_data.conversation_id,
        current_user.id,
        message_data
    )
    if not message:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return MessageRead.model_validate(message)