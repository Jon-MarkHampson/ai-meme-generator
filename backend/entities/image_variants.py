from uuid import uuid4
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, ForeignKey, CheckConstraint


class ImageVariant(SQLModel, table=True):
    __tablename__ = "image_variants"
    __table_args__ = (
        CheckConstraint(
            "variant_rank >= 0", name="ck_image_variants_variant_rank_non_negative"
        ),
    )

    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True, index=True)
    caption_variant_id: str = Field(
        sa_column=Column(
            ForeignKey("caption_variants.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
    )
    image_url: str = Field(nullable=False)
    variant_rank: int = Field(default=0, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self):
        return (
            f"CaptionVariant("
            f"id={self.id!r}, "
            f"image_url={self.image_url!r}, "
            f"variant_rank={self.variant_rank!r}, "
            f"created_at={self.created_at!r}"
            f")"
        )

    def __str__(self):
        return f"ImageVariant: {self.image_url} (ID: {self.id})"
