"""
SQLModel ORM table for Message entity.
Defines the database schema for conversation messages.
"""
from uuid import uuid4
from typing import List, Dict
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB


class Message(SQLModel, table=True):
    """
    Database model for conversation messages.
    
    Stores message data including:
    - Link to the parent conversation
    - JSON array of message objects (role, content, etc.)
    - Creation timestamp
    """
    __tablename__: str = "messages"

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