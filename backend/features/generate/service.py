from datetime import datetime, timezone
import json
import logging
from typing import List
import httpx
import asyncio
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from database.core import Session as SessionClass, engine
from openai import OpenAI
from openai.types.responses import WebSearchToolParam
from pydantic_ai.models.openai import (
    OpenAIResponsesModelSettings,
)

from pydantic_ai.messages import (
    ModelMessagesTypeAdapter,
    ModelRequest,
    ModelResponse,
    UserPromptPart,
    TextPart,
)

from entities.chat_conversations import Conversation as ConversationEntity
from entities.chat_messages import Message as MessageEntity
from entities.user import User
from .agent import manager_agent
from .models import (
    ConversationRead,
    ConversationUpdate,
    MessageRead,
    MessageCreate,
    ChatMessage,
    ConversationUpdateMessage,
    Deps,
)


logger = logging.getLogger(__name__)

client = OpenAI()


def list_conversations_ordered(
    session: Session, current_user: User
) -> List[ConversationRead]:
    stmt = (
        select(ConversationEntity)
        .where(ConversationEntity.user_id == current_user.id)
        .order_by(ConversationEntity.updated_at.desc())
    )
    convs = session.exec(stmt).all()
    return [c for c in convs]


def create_conversation(session: Session, current_user: User) -> ConversationRead:
    conv = ConversationEntity(user_id=current_user.id)
    session.add(conv)
    session.commit()
    session.refresh(conv)
    return conv


def get_conversation(
    conversation_id: str, session: Session, current_user: User
) -> ConversationRead:
    conv = session.get(ConversationEntity, conversation_id)
    if not conv or conv.user_id != current_user.id:
        return None
    return conv


def update_conversation(
    conversation_id: str,
    updates: ConversationUpdate,
    session: Session,
    current_user: User,
) -> ConversationRead:
    conv = session.get(ConversationEntity, conversation_id)
    if not conv or conv.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if updates.summary is not None:
        conv.summary = updates.summary
    conv.updated_at = datetime.now(timezone.utc)
    session.add(conv)
    session.commit()
    session.refresh(conv)
    return conv


def delete_conversation(
    conversation_id: str, session: Session, current_user: User
) -> None:
    conv = session.get(ConversationEntity, conversation_id)
    if not conv or conv.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    session.delete(conv)
    session.commit()


def list_messages(
    conversation_id: str,
    session: Session,
    current_user: User,
) -> List[ChatMessage]:
    out: List[ChatMessage] = []

    conv = session.get(ConversationEntity, conversation_id)
    if not conv or conv.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")

    stmt = (
        select(MessageEntity)
        .where(MessageEntity.conversation_id == conversation_id)
        .order_by(MessageEntity.created_at)
    )
    rows = session.exec(stmt).all()

    for row in rows:
        # row.message_list is already a Python list[dict]
        msgs = ModelMessagesTypeAdapter.validate_python(row.message_list)

        for m in msgs:
            # catch **all** user‐prompt parts, not just the first one
            if isinstance(m, ModelRequest):
                for part in m.parts:
                    if isinstance(part, UserPromptPart):
                        out.append(
                            ChatMessage(
                                role="user",
                                content=part.content,
                                timestamp=part.timestamp,
                            )
                        )

            # catch **all** text parts of the model response
            elif isinstance(m, ModelResponse):
                for part in m.parts:
                    if isinstance(part, TextPart):
                        out.append(
                            ChatMessage(
                                role="model",
                                content=part.content,
                                timestamp=m.timestamp,
                            )
                        )

    return out


def store_message(
    conversation_id: str,
    payload: MessageCreate,
    session: Session,
    current_user: User,
) -> MessageRead:
    conv = session.get(ConversationEntity, conversation_id)
    if not conv or conv.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    msg = MessageEntity(
        conversation_id=conversation_id,
        message_list=payload.message_list,
    )
    session.add(msg)
    session.commit()
    session.refresh(msg)
    return msg


def chat_stream(
    conversation_id: str,
    prompt: str,
    session: Session,
    current_user: User,
    manager_model: str = "gpt-4.1-2025-04-14",
) -> StreamingResponse:
    # Debug check the model being used
    logger.info(f"Using model: {manager_model}")

    # Check conversation exists first, then close this session
    conv = session.get(ConversationEntity, conversation_id)
    if not conv or conv.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Extract user ID before the session is closed to avoid DetachedInstanceError
    user_id = current_user.id

    async def streamer():
        user_msg = ChatMessage(
            role="user",
            content=prompt,
            timestamp=datetime.now(timezone.utc),
        )
        yield (user_msg.model_dump_json() + "\n").encode("utf-8")

        # Create a new session for the streaming operations
        # This prevents long-running connections from exhausting the pool

        with SessionClass(engine) as stream_session:
            try:
                # Re-fetch the user in the new session
                stream_current_user = stream_session.get(User, user_id)
                if not stream_current_user:
                    raise HTTPException(status_code=404, detail="User not found")

                stmt = select(MessageEntity).where(
                    MessageEntity.conversation_id == conversation_id
                )
                rows = stream_session.exec(stmt).all()
                history = []
                for row in rows:
                    history.extend(
                        ModelMessagesTypeAdapter.validate_json(
                            json.dumps(row.message_list)
                        )
                    )

                # Build dependencies with the new session
                deps = Deps(
                    client=client,
                    current_user=stream_current_user,
                    session=stream_session,
                    conversation_id=conversation_id,
                )
                model_settings = OpenAIResponsesModelSettings(
                    openai_builtin_tools=[WebSearchToolParam(type="web_search_preview")]
                )
                # ===== plain-text streaming =====
                try:
                    print(manager_agent.model_settings)
                    async with manager_agent.run_stream(
                        prompt,
                        # model=manager_model,
                        # model_settings=model_settings,
                        message_history=history,
                        deps=deps,
                    ) as result:
                        # use .stream_text to get raw LLM output (no JSON/schema parsing)
                        async for text_piece in result.stream_text(debounce_by=0.01):
                            # Check if this is a conversation update signal
                            if text_piece.startswith("CONVERSATION_UPDATE:"):
                                # Parse the conversation update
                                try:
                                    _, conv_id, summary, updated_at = text_piece.split(
                                        ":", 3
                                    )
                                    from .models import ConversationUpdateMessage

                                    update_msg = ConversationUpdateMessage(
                                        conversation_id=conv_id,
                                        summary=summary,
                                        updated_at=datetime.fromisoformat(updated_at),
                                    )
                                    yield (update_msg.model_dump_json() + "\n").encode(
                                        "utf-8"
                                    )
                                    continue  # Don't send this as a regular chat message
                                except Exception as e:
                                    logger.error(
                                        f"Error parsing conversation update: {e}"
                                    )
                                    # Fall through to send as regular message if parsing fails

                            # Send regular chat message
                            resp_msg = ChatMessage(
                                role="model",
                                content=text_piece,
                                timestamp=result.timestamp(),
                            )
                            yield (resp_msg.model_dump_json() + "\n").encode("utf-8")
                except (
                    BrokenPipeError,
                    ConnectionResetError,
                    OSError,
                    asyncio.CancelledError,
                    httpx.HTTPError,
                ):
                    # client disconnected; stop streaming gracefully
                    return
                except Exception as e:
                    # Handle other errors including OpenAI moderation errors
                    logger.error(f"Error in agent stream: {e}")

                    # Check if it's an OpenAI moderation error
                    error_message = str(e)
                    if (
                        "moderation_blocked" in error_message
                        or "safety system" in error_message
                    ):
                        error_resp = ChatMessage(
                            role="model",
                            content="I'm sorry, but I can't create that meme as it was flagged by the content safety system. "
                            "Please try a different caption or theme that doesn't contain potentially harmful content.",
                            timestamp=datetime.now(timezone.utc),
                        )
                    else:
                        error_resp = ChatMessage(
                            role="model",
                            content="I'm sorry, but I encountered an error while creating your meme. Please try again with a different request.",
                            timestamp=datetime.now(timezone.utc),
                        )

                    yield (error_resp.model_dump_json() + "\n").encode("utf-8")
                    return

                # Store the final result in the database
                full_json = result.new_messages_json()
                payload = json.loads(full_json)
                store_message(
                    conversation_id,
                    MessageCreate(
                        conversation_id=conversation_id, message_list=payload
                    ),
                    stream_session,
                    stream_current_user,
                )
                stream_session.commit()

            except Exception as e:
                stream_session.rollback()
                logger.error(f"Error in chat stream: {e}")
                raise

    return StreamingResponse(streamer(), media_type="text/plain")
