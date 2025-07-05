from sqlmodel import SQLModel, Session, create_engine
from entities.user import User
from entities.meme_templates import MemeTemplate
from entities.template_embeddings import TemplateEmbedding
from entities.caption_requests import CaptionRequest
from entities.caption_variants import CaptionVariant
from entities.user_memes import UserMeme
from entities.image_variants import ImageVariant
from entities.chat_converstaions import Conversation
from entities.chat_messages import Message


from config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,  # <-- makes SQLAlchemy check connections before using
    pool_recycle=3600,  # <-- optional: recycle connections every hour
    pool_size=10,  # adjust to required load
    max_overflow=20,
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
