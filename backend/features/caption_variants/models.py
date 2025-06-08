from datetime import datetime
from pydantic import BaseModel


class CaptionVariantCreate(BaseModel):
    request_id: str
    variant_rank: int = 0
    caption_text: list[str]
    model_name: str = ""  # Default to empty string if not specified


class CaptionVariantRead(BaseModel):
    id: str
    request_id: str
    variant_rank: int
    caption_text: list[str]
    model_name: str
    created_at: datetime  # ISO format string for datetime

    class Config:
        from_attributes = True  # Allows reading from SQLModel attributes


class CaptionVariantList(BaseModel):
    variants: list[CaptionVariantRead]

    class Config:
        from_attributes = True  # Allows reading from SQLModel attributes
