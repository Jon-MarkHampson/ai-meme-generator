from sqlmodel import SQLModel, Session, create_engine, text
from sqlalchemy.exc import OperationalError
from entities.user import User
from entities.meme_templates import MemeTemplate
from entities.template_embeddings import TemplateEmbedding
from entities.caption_requests import CaptionRequest
from entities.caption_variants import CaptionVariant
from entities.user_memes import UserMeme
from entities.image_variants import ImageVariant
from entities.chat_conversations import Conversation
from entities.chat_messages import Message
import logging

from config import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,  # makes SQLAlchemy check connections before using
    pool_recycle=300,  # recycle connections every 5 minutes (more aggressive)
    pool_size=10,  # reduced pool size to be more conservative
    max_overflow=20,  # reduced overflow
    pool_timeout=60,  # increased timeout to 60 seconds
    pool_reset_on_return="commit",  # reset connections on return
    connect_args={
        "sslmode": "require",
        "connect_timeout": 30,  # increased connection timeout
        "application_name": "ai-meme-generator",
        "keepalives_idle": 600,  # send keepalive every 10 minutes
        "keepalives_interval": 30,  # interval between keepalives
        "keepalives_count": 3,  # number of keepalives before giving up
    },
)


def create_db_and_tables():
    """Create all database tables based on SQLModel metadata."""
    SQLModel.metadata.create_all(engine)


# Shared session dependency with retry logic
def get_session():
    """
    FastAPI dependency that yields a new SQLModel Session
    and commits/rolls back automatically when the request ends.
    Includes proper error handling and connection cleanup with retry logic.
    """
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            session = Session(engine)
            try:
                yield session
                session.commit()
                return
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
        except OperationalError as e:
            retry_count += 1
            logger.warning(f"Database connection attempt {retry_count} failed: {e}")
            if retry_count >= max_retries:
                logger.error("Maximum database connection retries exceeded")
                raise
            # Wait a bit before retrying
            import time

            time.sleep(0.5 * retry_count)
        except Exception as e:
            logger.error(f"Unexpected database error: {e}")
            raise


def check_db_connection():
    """
    Check if the database connection is working properly.
    This can be used for health checks and debugging.
    """
    try:
        with Session(engine) as session:
            # Simple query to test connection
            session.exec(text("SELECT 1"))
            return True
    except OperationalError as e:
        logger.error(f"Database connection failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected database error: {e}")
        return False


def get_session_with_retry(max_retries: int = 3):
    """
    FastAPI dependency that yields a new SQLModel Session with retry logic.
    Includes proper error handling and connection cleanup.
    """
    retry_count = 0
    while retry_count < max_retries:
        try:
            session = Session(engine)
            try:
                yield session
                session.commit()
                break
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
        except OperationalError as e:
            retry_count += 1
            logger.warning(f"Database connection attempt {retry_count} failed: {e}")
            if retry_count >= max_retries:
                logger.error("Maximum database connection retries exceeded")
                raise
            # Wait a bit before retrying
            import time

            time.sleep(0.5 * retry_count)
        except Exception as e:
            logger.error(f"Unexpected database error: {e}")
            raise
