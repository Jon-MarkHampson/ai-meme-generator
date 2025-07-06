from dataclasses import dataclass
from openai import OpenAI
from pydantic import BaseModel
from typing import List, Dict, Literal, Optional
from datetime import datetime


# ─── Dependency Container ───────────────────────────────────────────────────
@dataclass
class Deps:
    client: OpenAI


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


class MemeCaptionAndContext(BaseModel):
    """
    Represents a single meme caption with top and bottom text.
    """

    text_boxes: Dict[str, str]  # Dictionary with keys 'text_box_1' and 'text_box_2'
    context: Optional[str] = None  # Optional context for the meme


class ImageResult(BaseModel):
    url: str  # the Supabase URL
    response_id: str  # the OpenAI `response.id` you got back
