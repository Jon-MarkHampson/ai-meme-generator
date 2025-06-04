from uuid import uuid4
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True, index=True)
    username: str = Field(index=True, nullable=False, unique=True)
    email: str = Field(index=True, nullable=False, unique=True)
    hashed_password: str = Field(nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self):
        return f"User(id={self.id}, username={self.username}, email={self.email}, password=****, created_at={self.created_at})"

    def __str__(self):
        return f"User: {self.username} <{self.email}> (ID: {self.id})"
