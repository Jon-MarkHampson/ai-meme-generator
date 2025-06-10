from uuid import uuid4
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, ForeignKey, String, CheckConstraint
from sqlalchemy.dialects.postgresql import ARRAY


class CaptionVariant(SQLModel, table=True):
    __tablename__ = "caption_variants"
    __table_args__ = (
        CheckConstraint(
            "variant_rank >= 0", name="ck_image_variants_variant_rank_non_negative"
        ),
    )

    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True, index=True)
    request_id: str = Field(
        sa_column=Column(
            ForeignKey("caption_requests.id", ondelete="CASCADE"), nullable=False
        ),
    )
    variant_rank: int = Field(default=0, nullable=False)
    caption_text: list[str] = Field(
        default_factory=list, sa_column=Column(ARRAY(String), nullable=False)
    )
    model_name: str = Field(default="", nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self):
        return (
            f"CaptionVariant("
            f"id={self.id!r}, "
            f"request_id={self.request_id!r}, "
            f"variant_rank={self.variant_rank!r}, "
            f"caption_text={self.caption_text!r}, "
            f"model_name={self.model_name!r}, "
            f"created_at={self.created_at!r}"
            f")"
        )

    def __str__(self):
        return f"CaptionVariant: {self.caption_text} (ID: {self.id})"
