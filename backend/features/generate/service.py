"""
Meme generation service orchestrating AI agents and streaming responses.

This service manages the complex workflow of AI-powered meme generation,
coordinating multiple specialized agents while streaming real-time updates
to the frontend. It handles conversation history, error recovery, and
content safety filtering.

Key responsibilities:
- Agent orchestration with configurable AI models
- Real-time streaming of generation progress
- Conversation history management
- Error handling with user-friendly messages
- Content moderation compliance
"""
import json
import logging
from datetime import datetime, timezone
import httpx
import asyncio
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from database.core import Session as SessionClass, engine
from openai import OpenAI
from pydantic_ai.messages import ModelMessagesTypeAdapter

from entities.messages import Message as MessageEntity
from entities.conversations import Conversation as ConversationEntity
from entities.user import User
from features.messages.models import ChatMessage, MessageCreate
from features.messages.service import create_message
from features.conversations.service import update_conversation as update_conversation_service
from features.conversations.models import ConversationUpdate
from .agent import create_manager_agent
from .models import Deps, ConversationUpdateSignal

logger = logging.getLogger(__name__)
client = OpenAI()


def generate_meme_stream(
    prompt: str,
    conversation_id: str,
    manager_model: str,
    session: Session,
    current_user: User,
) -> StreamingResponse:
    """
    Generate a meme using AI agents with streaming response.
    
    This function creates a streaming response that yields chat messages
    as the AI processes the request and generates meme content.
    
    Args:
        prompt: User's meme generation request
        conversation_id: ID of the conversation to add messages to
        manager_model: AI model to use in format "provider:model"
        session: Database session for queries
        current_user: Authenticated user making the request
        
    Returns:
        StreamingResponse that yields JSON chat messages
        
    Raises:
        ValueError: If conversation not found or user unauthorized
    """
    
    # Parse model selection format (e.g., "openai:gpt-4")
    provider, model = manager_model.split(":")
    logger.info(f"Using model: {model} from provider: {provider}")
    
    # Verify conversation ownership for security
    conversation = session.get(ConversationEntity, conversation_id)
    if not conversation or conversation.user_id != current_user.id:
        raise ValueError("Conversation not found")
    
    # Cache user ID to avoid database lookups in async context
    user_id = current_user.id
    
    async def streamer():
        """
        Async generator producing Server-Sent Event stream.
        
        Yields JSON-encoded messages as the AI processes the request,
        providing real-time feedback on meme generation progress.
        """
        # Echo user message immediately for UI responsiveness
        user_message = ChatMessage(
            role="user",
            content=prompt,
            timestamp=datetime.now(timezone.utc),
        )
        yield (user_message.model_dump_json() + "\n").encode("utf-8")
        
        # Create new session for async operations to avoid connection conflicts
        with SessionClass(engine) as stream_session:
            try:
                # Re-fetch user in new session context
                stream_current_user = stream_session.get(User, user_id)
                if not stream_current_user:
                    raise ValueError("User not found")
                
                # Load conversation history for context
                statement = select(MessageEntity).where(
                    MessageEntity.conversation_id == conversation_id
                )
                rows = stream_session.exec(statement).all()
                history = []
                for row in rows:
                    # Deserialize stored message history
                    history.extend(
                        ModelMessagesTypeAdapter.validate_json(
                            json.dumps(row.message_list)
                        )
                    )
                
                # Bundle dependencies for agent access
                dependencies = Deps(
                    client=client,
                    current_user=stream_current_user,
                    session=stream_session,
                    conversation_id=conversation_id,
                )
                
                # Create agent with selected AI model
                manager_agent = create_manager_agent(provider=provider, model=model)
                
                try:
                    # Stream agent responses with minimal buffering for responsiveness
                    async with manager_agent.run_stream(
                        prompt,
                        message_history=history,
                        deps=dependencies,
                    ) as result:
                        async for text_piece in result.stream_text(debounce_by=0.01):
                            # Handle special conversation update signals
                            if text_piece.startswith("CONVERSATION_UPDATE:"):
                                try:
                                    # Parse structured update signal
                                    _, conversation_id_value, summary, updated_at = text_piece.split(":", 3)
                                    update_message = ConversationUpdateSignal(
                                        conversation_id=conversation_id_value,
                                        summary=summary,
                                    )
                                    yield (update_message.model_dump_json() + "\n").encode("utf-8")
                                    
                                    # Persist conversation summary update
                                    update_conversation_service(
                                        stream_session,
                                        conversation_id_value,
                                        stream_current_user.id,
                                        ConversationUpdate(summary=summary)
                                    )
                                    continue
                                except Exception as e:
                                    logger.error(f"Error parsing conversation update: {e}")
                            
                            # Stream regular AI response content
                            response_message = ChatMessage(
                                role="model",
                                content=text_piece,
                                timestamp=result.timestamp(),
                            )
                            yield (response_message.model_dump_json() + "\n").encode("utf-8")
                
                except (
                    BrokenPipeError,
                    ConnectionResetError,
                    OSError,
                    asyncio.CancelledError,
                    httpx.HTTPError,
                ):
                    # Silently handle client disconnections
                    return
                except Exception as e:
                    logger.error(f"Error in agent stream: {e}")
                    
                    # Provide user-friendly error messages
                    error_message = str(e)
                    if "moderation_blocked" in error_message or "safety system" in error_message:
                        # Content safety violation - guide user to appropriate content
                        error_response = ChatMessage(
                            role="model",
                            content="I'm sorry, but I can't create that meme as it was flagged by the content safety system. "
                            "Please try a different caption or theme that doesn't contain potentially harmful content.",
                            timestamp=datetime.now(timezone.utc),
                        )
                    else:
                        # Generic error fallback
                        error_response = ChatMessage(
                            role="model",
                            content="I'm sorry, but I encountered an error while creating your meme. Please try again with a different request.",
                            timestamp=datetime.now(timezone.utc),
                        )
                    
                    yield (error_response.model_dump_json() + "\n").encode("utf-8")
                    return
                
                # Persist complete conversation exchange
                full_json = result.new_messages_json()
                payload = json.loads(full_json)
                create_message(
                    stream_session,
                    conversation_id,
                    stream_current_user.id,
                    MessageCreate(
                        conversation_id=conversation_id,
                        message_list=payload
                    ),
                )
                stream_session.commit()
            
            except Exception as e:
                # Ensure database consistency on errors
                stream_session.rollback()
                logger.error(f"Error in generate meme stream: {e}")
                raise
    
    return StreamingResponse(streamer(), media_type="text/plain")