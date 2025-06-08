from enum import Enum
from uuid import uuid4
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB, ARRAY


class TemplateSource(str, Enum):
    CLASSIC = "CLASSIC"
    AI_GENERATED = "AI_GENERATED"


class MemeTemplate(SQLModel, table=True):
    __tablename__ = "meme_templates"

    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True, index=True)
    name: str = Field(index=True, nullable=False, unique=True)
    description: str = Field(default="", nullable=True)
    image_url: str = Field(nullable=False)
    resolution_width: int = Field(default=500, nullable=False)
    resolution_height: int = Field(default=500, nullable=False)
    text_box_count: int = Field(default=2, nullable=False)
    text_box_coords: list[dict[str, int]] = Field(
        default_factory=list, sa_column=Column(JSONB, nullable=False)
    )
    keywords: list[str] = Field(
        default_factory=list, sa_column=Column(ARRAY(String), nullable=False)
    )  # ability to store e.g. ['leo','diCaprio','wine']
    source: TemplateSource = Field(default=TemplateSource.CLASSIC, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self):
        return (
            f"MemeTemplate("
            f"id={self.id!r}, "
            f"name={self.name!r}, "
            f"description={self.description!r}, "
            f"image_url={self.image_url!r}, "
            f"resolution_width={self.resolution_width}, "
            f"resolution_height={self.resolution_height}, "
            f"text_box_count={self.text_box_count}, "
            f"text_box_coords={self.text_box_coords!r}, "
            f"keywords={self.keywords!r}, "
            f"source={self.source!r}, "
            f"created_at={self.created_at!r}"
            f")"
        )

    def __str__(self):
        return f"MemeTemplate: {self.name} (ID: {self.id}) - {self.image_url}"
