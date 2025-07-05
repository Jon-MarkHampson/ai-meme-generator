import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from database.core import get_session
from features.auth.service import get_current_user
from entities.user import User
from .models import (
    ConversationRead,
    ConversationUpdate,
    MessageRead,
    MessageCreate,
    ChatRequest,
    ChatMessage,
)
from .service import (
    list_conversations,
    create_conversation,
    get_conversation,
    update_conversation,
    delete_conversation,
    list_messages,
    store_message,
    chat_stream,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/generate", tags=["generate"])

# Conversation CRUD


@router.get(
    "/conversations/",
    response_model=List[ConversationRead],
    summary="List all conversations for the current user.",
)
def read_conversations(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[ConversationRead]:
    logger.info(f"Listing conversations for user {current_user.id}")
    return list_conversations(session, current_user)


@router.post(
    "/conversations/",
    response_model=ConversationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new conversation.",
)
def start_conversation(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ConversationRead:
    logger.info(f"Creating conversation for user {current_user.id}")
    return create_conversation(session, current_user)


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationRead,
    summary="Get a single conversation.",
)
def read_conversation_route(
    conversation_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ConversationRead:
    conv = get_conversation(conversation_id, session, current_user)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.patch(
    "/conversations/{conversation_id}",
    response_model=ConversationRead,
    summary="Update a conversation's summary.",
)
def patch_conversation(
    conversation_id: str,
    updates: ConversationUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ConversationRead:
    logger.info(f"Updating conversation {conversation_id} for user {current_user.id}")
    return update_conversation(conversation_id, updates, session, current_user)


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a conversation.",
)
def delete_conversation_route(
    conversation_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    logger.info(f"Deleting conversation {conversation_id} for user {current_user.id}")
    delete_conversation(conversation_id, session, current_user)


# Message CRUD


@router.get(
    "/conversations/{conversation_id}/messages/",
    response_model=List[ChatMessage],
    summary="List all messages in a conversation.",
)
def read_messages(
    conversation_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[ChatMessage]:
    return list_messages(conversation_id, session, current_user)


@router.post(
    "/conversations/{conversation_id}/messages/",
    response_model=MessageRead,
    status_code=status.HTTP_201_CREATED,
    summary="Append a message to a conversation.",
)
def post_message(
    conversation_id: str,
    payload: MessageCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> MessageRead:
    return store_message(conversation_id, payload, session, current_user)


# Streaming chat endpoint


@router.post(
    "/conversations/{conversation_id}/stream/",
    summary="Stream chat within a conversation.",
)
def stream_conversation(
    conversation_id: str,
    request: ChatRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """
    Opens a streaming response that yields newline-delimited JSON ChatMessage objects.
    """
    return chat_stream(conversation_id, request.prompt, session, current_user)
