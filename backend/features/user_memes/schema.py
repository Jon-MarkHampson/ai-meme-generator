from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserMemeCreate(BaseModel):
    conversation_id: str
    image_url: str
    openai_response_id: str  # This is the ID from OpenAI's response
    is_favorite: bool = False  # Default to False if not specified


class UserMemeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    conversation_id: str
    image_url: str
    openai_response_id: str  # This is the ID from OpenAI's response
    is_favorite: bool
    created_at: datetime  # ISO format string for datetime


class UserMemeUpdate(BaseModel):
    is_favorite: Optional[bool] = None  # Default to None if not specified


class UserMemeList(BaseModel):
    memes: list[UserMemeRead]
