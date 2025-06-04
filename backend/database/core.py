from pathlib import Path

from sqlmodel import SQLModel, Session, create_engine
from entities.user import User
from config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=True,
    connect_args={"sslmode": "require"},  # enforce SSL for Supabase
)


def create_db_and_tables():
    """Create all database tables based on SQLModel metadata."""
    SQLModel.metadata.create_all(engine)


# Shared session dependency
def get_session():
    """
    FastAPI dependency that yields a new SQLModel Session
    and commits/rolls back automatically when the request ends.
    """
    with Session(engine) as session:
        yield session
