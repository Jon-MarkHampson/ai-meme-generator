from uuid import uuid4
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field


class UserMeme(SQLModel, table=True):
    __tablename__ = "user_memes"

    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True, index=True)
    user_id: str = Field(
        foreign_key="users.id",
        nullable=False,
        sa_column_kwargs={"ondelete": "CASCADE"},
    )
    meme_template_id: str = Field(
        foreign_key="meme_templates.id",
        nullable=False,
        sa_column_kwargs={"ondelete": "CASCADE"},
    )
    image_url: str = Field(nullable=False)
    is_favorite: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self):
        return (
            f"UserMemes("
            f"id={self.id!r}, "
            f"user_id={self.user_id!r}, "
            f"meme_template_id={self.meme_template_id!r}, "
            f"image_url={self.image_url!r}, "
            f"is_favorite={self.is_favorite!r}, "
            f"created_at={self.created_at!r}"
            f")"
        )

    def __str__(self):
        return (
            f"UserMemes: User {self.user_id} created meme template {self.meme_template_id} "
            f"on {self.created_at} favorited: {self.is_favorite}"
        )
