from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ConversationCreate(BaseModel):
    pass


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    summary: Optional[str]
    created_at: datetime
    updated_at: datetime


class ConversationUpdate(BaseModel):
    summary: Optional[str] = None