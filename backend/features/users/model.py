"""
SQLModel ORM table for User entity.
Defines the database schema for user accounts.
"""
from uuid import uuid4
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime


class User(SQLModel, table=True):
    """
    Database model for user accounts.
    
    Stores user authentication and profile information including:
    - Unique identifier (UUID hex)
    - Name and email
    - Hashed password for authentication
    - Account creation timestamp
    """
    __tablename__: str = "users"

    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True, index=True)
    first_name: str = Field(index=True, nullable=False)
    last_name: str = Field(index=True, nullable=False)
    email: str = Field(index=True, nullable=False, unique=True)
    hashed_password: str = Field(nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            nullable=False,
        ),
    )

    def __repr__(self):
        return f"User(id={self.id}, first_name={self.first_name}, last_name={self.last_name}, email={self.email}, password=****, created_at={self.created_at})"

    def __str__(self):
        return (
            f"User: {self.first_name} {self.last_name} <{self.email}> (ID: {self.id})"
        )