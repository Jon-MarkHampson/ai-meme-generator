from uuid import uuid4
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, Float
from sqlalchemy.dialects.postgresql import ARRAY


class TemplateEmbedding(SQLModel, table=True):
    __tablename__ = "template_embeddings"

    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True, index=True)
    template_id: str = Field(index=True, nullable=False)
    embedding: list[float] = Field(
        default_factory=list, sa_column=Column(ARRAY(Float), nullable=False)
    )
    # Whether the embedding has been indexed in the vector database
    indexed: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            nullable=False,
        ),
    )

    def __repr__(self):
        return (
            f"TemplateEmbedding("
            f"id={self.id!r}, "
            f"template_id={self.template_id!r}, "
            f"embedding={self.embedding!r}, "
            f"created_at={self.created_at!r}"
            f")"
        )

    def __str__(self):
        return f"TemplateEmbedding: {self.template_id} (ID: {self.id}) - Created at {self.created_at}"
