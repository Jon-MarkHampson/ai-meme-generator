from datetime import datetime, timezone
import json
import logging
from typing import List

from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from pydantic_ai.messages import (
    ModelMessagesTypeAdapter,
    ModelRequest,
    ModelResponse,
    UserPromptPart,
    TextPart,
)

from entities.chat_converstaions import Conversation as ConversationEntity
from entities.chat_messages import Message as MessageEntity
from entities.user import User
from .agent import chat_agent
from .models import (
    ConversationRead,
    ConversationUpdate,
    MessageRead,
    MessageCreate,
    ChatMessage,
)

logger = logging.getLogger(__name__)


def list_conversations(session: Session, current_user: User) -> List[ConversationRead]:
    stmt = select(ConversationEntity).where(
        ConversationEntity.user_id == current_user.id
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
    # Start with an empty list to collect messages to avoid returning None
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
            first = m.parts[0]
            if isinstance(m, ModelRequest) and isinstance(first, UserPromptPart):
                out.append(
                    ChatMessage(
                        role="user",
                        content=first.content,
                        timestamp=first.timestamp,
                    )
                )
            elif isinstance(m, ModelResponse) and isinstance(first, TextPart):
                out.append(
                    ChatMessage(
                        role="model",
                        content=first.content,
                        timestamp=m.timestamp,
                    )
                )
    return out


def create_message(
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
) -> StreamingResponse:
    async def streamer():
        user_msg = ChatMessage(
            role="user",
            content=prompt,
            timestamp=datetime.now(timezone.utc),
        )
        yield (user_msg.model_dump_json() + "\n").encode("utf-8")

        stmt = select(MessageEntity).where(
            MessageEntity.conversation_id == conversation_id
        )
        rows = session.exec(stmt).all()
        history = []
        for row in rows:
            history.extend(
                ModelMessagesTypeAdapter.validate_json(json.dumps(row.message_list))
            )

        async with chat_agent.run_stream(prompt, message_history=history) as result:
            async for chunk in result.stream(debounce_by=0.01):
                resp_msg = ChatMessage(
                    role="model",
                    content=chunk,
                    timestamp=result.timestamp(),
                )
                yield (resp_msg.model_dump_json() + "\n").encode("utf-8")

        full_json = result.new_messages_json()
        payload = json.loads(full_json)
        create_message(
            conversation_id,
            MessageCreate(conversation_id=conversation_id, message_list=payload),
            session,
            current_user,
        )

    conv = session.get(ConversationEntity, conversation_id)
    if not conv or conv.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return StreamingResponse(streamer(), media_type="text/plain")
