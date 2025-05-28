from sqlmodel import SQLModel, create_engine
from app.models.hero import Hero

# SQL file-based DB
DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)