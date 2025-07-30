from uuid import uuid4
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, ForeignKey


class Conversation(SQLModel, table=True):
    __tablename__: str = "conversations"

    id: str = Field(
        default_factory=lambda: uuid4().hex,
        primary_key=True,
        index=True,
    )
    user_id: str = Field(
        sa_column=Column(
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
    )
    summary: Optional[str] = Field(default=None, nullable=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            nullable=False,
        ),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            onupdate=lambda: datetime.now(timezone.utc),
            nullable=False,
        ),
    )

    def __repr__(self):
        return (
            f"Conversation("
            f"id={self.id!r}, "
            f"user_id={self.user_id!r}, "
            f"summary={self.summary!r}, "
            f"created_at={self.created_at!r}, "
            f"updated_at={self.updated_at!r}"
            f")"
        )

    def __str__(self):
        return (
            f"Conversation: User {self.user_id} started a conversation "
            f"on {self.created_at} with summary: {self.summary}"
        )
