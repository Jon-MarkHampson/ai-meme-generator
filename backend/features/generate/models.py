from pydantic import BaseModel
from typing import List, Dict, Literal, Optional
from datetime import datetime


class ConversationRead(BaseModel):
    id: str
    user_id: str
    summary: Optional[str]
    created_at: datetime
    updated_at: datetime


class ConversationUpdate(BaseModel):
    summary: Optional[str] = None


class MessageRead(BaseModel):
    id: str
    conversation_id: str
    message_list: List[Dict]
    created_at: datetime


class MessageCreate(BaseModel):
    conversation_id: str
    message_list: List[Dict]


# Chat-only models (for the streaming API)
class ChatMessage(BaseModel):
    role: Literal["user", "model"]
    content: str
    timestamp: datetime


class ChatRequest(BaseModel):
    prompt: str


class ChatResponse(BaseModel):
    lines: List[ChatMessage]


class MemeCaption(BaseModel):
    """
    Represents a single meme caption with top and bottom text.
    """

    text_box_1: str  # Top text
    text_box_2: str  # Bottom text


class ResponseMemeCaptions(BaseModel):
    """
    Wrapper schema for a list of MemeCaption objects.
    """

    captions: list[MemeCaption]
