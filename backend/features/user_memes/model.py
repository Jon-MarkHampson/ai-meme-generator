"""
SQLModel ORM table for UserMeme entity.
Defines the database schema for user-generated memes.
"""
from uuid import uuid4
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, ForeignKey


class UserMeme(SQLModel, table=True):
    """
    Database model for user-generated memes.
    
    Stores information about memes created by users including:
    - Link to the conversation where it was generated
    - User who created it (with cascade delete)
    - Image URL for the generated meme
    - AI response tracking
    - Favorite status for user collections
    """
    __tablename__: str = "user_memes"

    # Primary key using hex UUID for better URL compatibility
    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True, index=True)
    
    # Foreign key relationships with cascade delete for data integrity
    conversation_id: str = Field(
        sa_column=Column(
            ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    user_id: str = Field(
        sa_column=Column(
            ForeignKey("users.id", ondelete="CASCADE"), 
            nullable=False, 
            index=True
        ),
    )
    
    # Meme data and metadata
    image_url: str = Field(nullable=False)  # URL to generated meme image
    openai_response_id: str = Field(nullable=False)  # AI response tracking
    is_favorite: bool = Field(default=False, nullable=False)  # User favorite status
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), 
        nullable=False
    )

    def __repr__(self):
        """Developer-friendly representation showing all fields."""
        return (
            f"UserMeme("
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
        """Human-readable description of the meme."""
        return (
            f"UserMeme: User {self.user_id} created meme {self.id} "
            f"on {self.created_at} (favorited: {self.is_favorite})"
        )