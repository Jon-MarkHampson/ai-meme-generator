from uuid import uuid4
from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, ForeignKey


class UserMeme(SQLModel, table=True):
    __tablename__: str = "user_memes"

    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True, index=True)
    conversation_id: str = Field(
        sa_column=Column(
            ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    user_id: str = Field(
        sa_column=Column(
            ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
        ),
    )
    image_url: str = Field(nullable=False)
    openai_response_id: str = Field(nullable=False)
    is_favorite: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self):
        return (
            f"UserMemes("
            f"id={self.id!r}, "
            f"conversation_id={self.conversation_id!r}, "
            f"user_id={self.user_id!r}, "
            f"image_url={self.image_url!r}, "
            f"openai_response_id={self.openai_response_id!r}, "
            f"is_favorite={self.is_favorite!r}, "
            f"created_at={self.created_at!r}"
            f")"
        )

    def __str__(self):
        return (
            f"UserMemes: User {self.user_id} created a meme with ID {self.id} "
            f"on {self.created_at} favorited: {self.is_favorite}"
        )
