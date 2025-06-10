from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from entities.user_memes import UserMeme


class UserMemeCreate(BaseModel):
    meme_template_id: Optional[str] = (
        None  # Remove optional once meme templates table is created
    )
    caption_variant_id: Optional[str] = None
    image_url: str
    is_favorite: Optional[bool] = False  # Default to False if not specified


class UserMemeRead(BaseModel):
    id: str
    user_id: str
    meme_template_id: Optional[str] = (
        None  # Remove optional once meme templates table is created
    )
    caption_variant_id: Optional[str] = None
    image_url: str
    is_favorite: bool
    created_at: datetime  # ISO format string for datetime

    class Config:
        from_attributes = True  # Allows reading from SQLModel attributes


class UserMemeUpdate(BaseModel):
    is_favorite: Optional[bool] = None  # Default to None if not specified

    class Config:
        from_attributes = True  # Allows reading from SQLModel attributes


class UserMemeList(BaseModel):
    memes: list[UserMemeRead]

    class Config:
        from_attributes = True  # Allows reading from SQLModel attributes
