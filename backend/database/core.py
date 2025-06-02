from pathlib import Path

from sqlmodel import SQLModel, Session, create_engine
from entities.user import User


# SQL file-based DB: use absolute path to ensure correct location
base_dir = Path(__file__).resolve().parent.parent  # backend/db -> backend
db_file = base_dir / "database.db"
DATABASE_URL = f"sqlite:///{db_file}"
engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    """Create all database tables based on SQLModel metadata."""
    SQLModel.metadata.create_all(engine)


# Shared session dependency
def get_session():
    """Yield a SQLModel session and handle commit/rollback automatically."""
    """
    FastAPI dependency that yields a new SQLModel Session
    and commits/rolls back automatically when the request ends.
    """
    with Session(engine) as session:
        yield session
