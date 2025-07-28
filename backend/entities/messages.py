from uuid import uuid4
from typing import List, Dict
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB


class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: str = Field(
        default_factory=lambda: uuid4().hex,
        primary_key=True,
        index=True,
    )
    conversation_id: str = Field(
        sa_column=Column(
            ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    message_list: List[Dict] = Field(
        sa_column=Column(JSONB, nullable=False),
        description="The full array of ModelMessage JSON objects",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            nullable=False,
        ),
    )
