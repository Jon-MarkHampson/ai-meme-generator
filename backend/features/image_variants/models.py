from datetime import datetime
from pydantic import BaseModel, Field
from entities.image_variants import ImageVariant


class ImageVariantCreate(BaseModel):
    caption_variant_id: str
    image_url: str
    variant_rank: int = Field(0, ge=0)  # Default to 0 if not specified, must be >= 0


class ImageVariantRead(BaseModel):
    id: str
    caption_variant_id: str
    image_url: str
    variant_rank: int
    created_at: datetime  # ISO format string for datetime

    class Config:
        from_attributes = True  # Allows reading from SQLModel attributes


class ImageVariantList(BaseModel):
    variants: list[ImageVariantRead]

    class Config:
        from_attributes = True  # Allows reading from SQLModel attributes
