from typing import List, Dict, Literal
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class MessageCreate(BaseModel):
    conversation_id: str
    message_list: List[Dict]


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    conversation_id: str
    message_list: List[Dict]
    created_at: datetime


class ChatMessage(BaseModel):
    role: Literal["user", "model"]
    content: str
    timestamp: datetime