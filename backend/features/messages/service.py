"""
Message management service handling conversation history and AI response storage.

This service manages the complex data transformation between Pydantic AI's internal
message format and the frontend chat interface. It handles persistence of conversation
exchanges while maintaining proper user ownership and security.

Key responsibilities:
- Message CRUD operations with ownership validation
- Complex message format transformation for AI system integration
- Conversation history management for context preservation
- Security enforcement to prevent cross-user data access

Technical note:
Pydantic AI uses a sophisticated message format that includes metadata like
timestamps, message parts, and role information. This service transforms
those complex structures into simple chat messages for the frontend.
"""
from typing import List, Optional

from pydantic_ai.messages import (ModelMessagesTypeAdapter, ModelRequest,
                                  ModelResponse, TextPart, UserPromptPart)
from sqlmodel import Session, select

from features.conversations.model import Conversation
from features.messages.model import Message

from .schema import ChatMessage, MessageCreate


def list_messages_by_conversation(
    session: Session,
    conversation_id: str,
    user_id: str
) -> List[Message]:
    """
    Retrieve all messages for a specific conversation with ownership validation.
    
    This function enforces security by verifying the user owns the conversation
    before returning any message data. Messages are returned in chronological
    order to maintain conversation flow.
    
    Args:
        session: Database session for executing queries
        conversation_id: UUID of the conversation to retrieve messages from
        user_id: ID of the user requesting the messages (for ownership check)
        
    Returns:
        List of Message entities in chronological order, or empty list if:
        - Conversation doesn't exist
        - User doesn't own the conversation
        - No messages exist in the conversation
        
    Security note:
        The ownership check prevents users from accessing other users'
        private conversation history, which is critical for data privacy.
    """
    # Verify conversation exists and user has access rights
    conversation = session.get(Conversation, conversation_id)
    if not conversation or conversation.user_id != user_id:
        return []  # Return empty list for security (don't reveal existence)
    
    # Query messages in chronological order for proper conversation flow
    statement = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    return list(session.exec(statement).all())


def create_message(
    session: Session,
    conversation_id: str,
    user_id: str,
    message_data: MessageCreate
) -> Optional[Message]:
    """
    Persist a complete conversation exchange to the database.
    
    This function stores the entire message exchange (user prompt + AI response)
    from a single generation request. The message_list contains the raw Pydantic AI
    message format which preserves all metadata needed for future context.
    
    Args:
        session: Database session for transaction management
        conversation_id: UUID of the target conversation
        user_id: ID of the user creating the message (for ownership validation)
        message_data: MessageCreate containing the Pydantic AI message list
        
    Returns:
        Created Message entity with generated ID and timestamp, or None if:
        - Conversation doesn't exist
        - User doesn't own the conversation
        - Database transaction fails
        
    Note:
        This function is called after streaming completes to persist the
        entire conversation exchange for future reference and context.
    """
    # Validate conversation ownership before allowing message creation
    conversation = session.get(Conversation, conversation_id)
    if not conversation or conversation.user_id != user_id:
        return None  # Prevent unauthorized message creation
    
    # Create message record with Pydantic AI message format
    message = Message(
        conversation_id=conversation_id,
        message_list=message_data.message_list  # Raw AI framework format
    )
    
    # Persist message with atomic transaction
    session.add(message)
    session.commit()
    session.refresh(message)  # Get generated timestamp and ID
    return message


def convert_messages_to_chat_format(messages: List[Message]) -> List[ChatMessage]:
    """
    Transform complex Pydantic AI message format into simple chat messages.
    
    This function bridges the gap between the AI framework's sophisticated
    message structure and the frontend's simple chat interface. It extracts
    user prompts and AI responses while preserving timestamps and content.
    
    The transformation process:
    1. Deserialize stored Pydantic AI message lists
    2. Extract text content from various message part types
    3. Convert to simple role/content/timestamp format
    4. Maintain chronological order for conversation flow
    
    Args:
        messages: List of Message entities from database containing raw AI format
        
    Returns:
        List of ChatMessage objects ready for frontend consumption
        
    Technical details:
        - ModelRequest objects contain user prompts (UserPromptPart)
        - ModelResponse objects contain AI responses (TextPart)
        - Complex nested structure is flattened to simple chat format
        - Timestamps are preserved for accurate conversation history
    """
    chat_messages: List[ChatMessage] = []
    
    # Process each stored message exchange
    for message in messages:
        # Deserialize Pydantic AI message format from database
        model_messages = ModelMessagesTypeAdapter.validate_python(message.message_list)
        
        # Extract content from complex message structure
        for model_message in model_messages:
            # Handle user prompts (input messages)
            if isinstance(model_message, ModelRequest):
                for part in model_message.parts:
                    if isinstance(part, UserPromptPart):
                        chat_messages.append(
                            ChatMessage(
                                role="user",
                                content=part.content,
                                timestamp=part.timestamp,
                            )
                        )
            
            # Handle AI responses (output messages)
            elif isinstance(model_message, ModelResponse):
                for part in model_message.parts:
                    if isinstance(part, TextPart):
                        chat_messages.append(
                            ChatMessage(
                                role="model",
                                content=part.content,
                                timestamp=model_message.timestamp,
                            )
                        )
    
    return chat_messages