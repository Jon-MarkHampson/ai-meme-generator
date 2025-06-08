from enum import Enum
from uuid import uuid4
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from typing import Optional


class RequestMethod(str, Enum):
    DIRECT = "DIRECT"
    AI_THEME = "AI_THEME"
    AI_FREEFORM = "AI_FREEFORM"


class CaptionRequest(SQLModel, table=True):
    __tablename__ = "caption_requests"

    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True, index=True)
    user_id: str = Field(nullable=False)
    meme_template_id: Optional[str] = Field(
        foreign_key="meme_templates.id",
        default=None,
        nullable=True,
        sa_column_kwargs={"ondelete": "CASCADE"},
    )
    request_method: RequestMethod = Field(default=RequestMethod.DIRECT, nullable=False)
    prompt_text: str = Field(nullable=False)
    chosen_variant_id: Optional[str] = Field(
        foreign_key="caption_variants.id",
        default=None,
        nullable=True,
        sa_column_kwargs={"ondelete": "CASCADE"},
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self):
        return (
            f"CaptionRequest("
            f"id={self.id!r}, "
            f"user_id={self.user_id!r}, "
            f"meme_template_id={self.meme_template_id!r}, "
            f"request_method={self.request_method!r}, "
            f"prompt_text={self.prompt_text!r}, "
            f"chosen_variant_id={self.chosen_variant_id!r}, "
            f"created_at={self.created_at!r}"
            f")"
        )

    def __str__(self):
        return (
            f"CaptionRequest: {self.prompt_text} (ID: {self.id}) - "
            f"User: {self.user_id}, Template: {self.meme_template_id}, "
            f"Method: {self.request_method}, Created at: {self.created_at}"
        )
