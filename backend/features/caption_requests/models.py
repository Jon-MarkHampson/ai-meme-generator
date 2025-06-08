from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from entities.caption_requests import RequestMethod


class CaptionRequestCreate(BaseModel):
    meme_template_id: Optional[str] = None
    request_method: RequestMethod = (
        RequestMethod.DIRECT
    )  # Default to DIRECT if not specified
    prompt_text: str


class CaptionRequestRead(BaseModel):
    id: str
    user_id: str
    meme_template_id: Optional[str] = None
    request_method: RequestMethod
    prompt_text: str
    chosen_variant_id: Optional[str] = None
    created_at: datetime  # ISO format string for datetime

    class Config:
        from_attributes = True  # Allows reading from SQLModel attributes


class CaptionRequestUpdate(BaseModel):
    meme_template_id: Optional[str] = None
    chosen_variant_id: Optional[str] = None


class CaptionRequestDelete(BaseModel):
    id: str
    user_id: str

    class Config:
        from_attributes = True  # Allows reading from SQLModel attributes


class CaptionRequestList(BaseModel):
    requests: list[CaptionRequestRead]

    class Config:
        from_attributes = True  # Allows reading from SQLModel attributes
