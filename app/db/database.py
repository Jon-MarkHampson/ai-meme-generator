from sqlmodel import SQLModel, Session, create_engine
from app.models.hero import Hero

# SQL file-based DB
DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    

# Shared session dependency
def get_session():
    """
    FastAPI dependency that yields a new SQLModel Session
    and commits/rolls back automatically when the request ends.
    """
    with Session(engine) as session:
        yield session