"""
Conversation controller managing chat session endpoints for meme generation.

This module provides HTTP endpoints for managing conversation threads that
organize user interactions with the AI meme generator. Each conversation
represents a distinct chat session where users can generate multiple memes
while maintaining context and history.

Key features:
- Complete CRUD operations for conversation management
- Ownership-based access control ensuring privacy
- Session organization for contextual meme generation
- RESTful API design with proper status codes
- Automatic conversation lifecycle management

Business context:
Conversations serve as containers for related meme generation requests,
allowing users to build on previous interactions and maintain thematic
consistency across multiple generations within a single session.

Security considerations:
- All endpoints require authenticated users
- Users can only access their own conversations
- Conversation ownership is enforced at the service layer
- Proper HTTP status codes provide clear API responses
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from database.core import get_session
from features.auth.service import get_current_user
from entities.user import User
from .models import ConversationRead, ConversationUpdate
from .service import (
    list_conversations,
    create_conversation,
    get_conversation,
    update_conversation,
    delete_conversation,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get(
    "/",
    response_model=List[ConversationRead],
    summary="List all conversations for the current user",
)
def read_conversations(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[ConversationRead]:
    """
    Retrieve all conversations belonging to the authenticated user.
    
    Used by the frontend to populate conversation history in chat interfaces,
    allowing users to resume previous meme generation sessions or browse
    their conversation archive. Results are typically ordered by recency.
    
    Args:
        session: Database session from dependency injection
        current_user: Authenticated user from JWT token validation
        
    Returns:
        List[ConversationRead]: All user conversations with metadata
        
    Usage context:
        Called when loading the main chat interface to show available
        conversation threads for continuation or reference.
        
    Note:
        Currently returns all conversations without pagination. Consider
        adding pagination for users with extensive conversation history.
    """
    logger.info(f"Listing conversations for user {current_user.id}")
    conversations = list_conversations(session, current_user.id)
    return [ConversationRead.model_validate(conv) for conv in conversations]


@router.post(
    "/",
    response_model=ConversationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new conversation",
)
def start_conversation(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ConversationRead:
    """
    Initialize a new conversation thread for meme generation.
    
    Creates a fresh conversation context that will contain all related
    meme generation requests and AI responses. Each conversation maintains
    its own context and history, allowing for thematic continuity.
    
    Args:
        session: Database session for persistence operations
        current_user: Authenticated user from JWT token validation
        
    Returns:
        ConversationRead: Newly created conversation with generated ID
        
    Usage context:
        Called when users start a new chat session or want to begin
        a fresh topic without carrying over previous conversation context.
        
    Business logic:
        - Automatically associates conversation with authenticated user
        - Generates unique conversation ID for future message routing
        - Sets initial timestamp for conversation tracking
    """
    logger.info(f"Creating conversation for user {current_user.id}")
    conversation = create_conversation(session, current_user.id)
    return ConversationRead.model_validate(conversation)


@router.get(
    "/{conversation_id}",
    response_model=ConversationRead,
    summary="Get a single conversation",
)
def read_conversation(
    conversation_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ConversationRead:
    """
    Retrieve a specific conversation by its unique identifier.
    
    Used when loading a particular conversation for continuation or
    when the frontend needs detailed conversation metadata. Enforces
    ownership validation to ensure privacy.
    
    Args:
        conversation_id: Unique identifier of the conversation to retrieve
        session: Database session from dependency injection
        current_user: Authenticated user from JWT token validation
        
    Returns:
        ConversationRead: Complete conversation data with metadata
        
    Raises:
        HTTPException: 404 if conversation not found or not owned by user
        
    Security note:
        Ownership validation prevents users from accessing other users'
        private conversation history through ID enumeration attacks.
        
    Usage context:
        Called when resuming a specific conversation or when displaying
        conversation details in management interfaces.
    """
    conversation = get_conversation(session, conversation_id, current_user.id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationRead.model_validate(conversation)


@router.patch(
    "/{conversation_id}",
    response_model=ConversationRead,
    summary="Update a conversation",
)
def patch_conversation(
    conversation_id: str,
    updates: ConversationUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ConversationRead:
    """
    Update conversation properties such as title or metadata.
    
    Allows users to modify conversation attributes like titles for better
    organization or other metadata fields. Uses PATCH semantics to support
    partial updates - only provided fields are modified.
    
    Args:
        conversation_id: Unique identifier of the conversation to update
        updates: Update payload with fields to modify
        session: Database session for persistence operations
        current_user: Authenticated user from JWT token validation
        
    Returns:
        ConversationRead: Updated conversation with new field values
        
    Raises:
        HTTPException: 404 if conversation not found or not owned by user
        HTTPException: 422 if update data format is invalid
        
    Usage context:
        Typically called when users rename conversations for better
        organization or when updating conversation settings.
        
    Business logic:
        - Only the conversation owner can make updates
        - Changes take effect immediately
        - Updated data is returned for frontend state synchronization
    """
    logger.info(f"Updating conversation {conversation_id} for user {current_user.id}")
    conversation = update_conversation(session, conversation_id, current_user.id, updates)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationRead.model_validate(conversation)


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a conversation",
)
def delete_conversation_route(
    conversation_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Permanently delete a conversation and its associated messages.
    
    Removes the conversation thread and all related message history from
    the system. This is a destructive operation that cannot be undone,
    so frontend should implement confirmation dialogs.
    
    Args:
        conversation_id: Unique identifier of the conversation to delete
        session: Database session for transaction management
        current_user: Authenticated user from JWT token validation
        
    Returns:
        None: 204 No Content status indicates successful deletion
        
    Raises:
        HTTPException: 404 if conversation not found or not owned by user
        
    Data implications:
        - Conversation metadata is permanently removed
        - All associated messages within the conversation are deleted
        - Related meme records may be preserved depending on business logic
        
    Security considerations:
        - Only the conversation owner can delete their conversations
        - Operation is logged for audit purposes
        - Cascading deletion may affect related entities
        
    Important:
        Users should be warned about data loss before confirming deletion
        as this action cannot be reversed once completed.
    """
    logger.info(f"Deleting conversation {conversation_id} for user {current_user.id}")
    success = delete_conversation(session, conversation_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")