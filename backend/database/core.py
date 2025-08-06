"""
Database connection and session management for the AI Meme Generator.
Provides SQLModel engine configuration with connection pooling and retry logic.
"""
import logging
from sqlmodel import SQLModel, Session, create_engine, text
from sqlalchemy.exc import OperationalError

from config import settings
# Import models registry to ensure all models are registered before creating tables
import models_registry

logger = logging.getLogger(__name__)

# Database engine with production-ready connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,  # Test connections before use
    pool_recycle=300,  # Recycle connections every 5 minutes
    pool_size=10,  # Base connection pool size
    max_overflow=20,  # Additional connections when needed
    pool_timeout=60,  # Wait time for connection from pool
    pool_reset_on_return="commit",  # Clean state on connection return
    connect_args={
        "sslmode": "require",  # Force SSL for security
        "connect_timeout": 30,  # Connection establishment timeout
        "application_name": "ai-meme-generator",  # For DB monitoring
        "keepalives_idle": 600,  # TCP keepalive settings for stability
        "keepalives_interval": 30,
        "keepalives_count": 3,
    },
)


def create_db_and_tables():
    """
    Create all database tables using SQLModel metadata.
    
    This function should be called during application startup to ensure
    all required tables exist. Uses SQLModel's automatic table creation
    based on the defined entity models.
    """
    SQLModel.metadata.create_all(engine)


def get_session():
    """
    FastAPI dependency that provides database sessions with automatic cleanup.
    
    This generator function yields a SQLModel Session that automatically:
    - Commits transactions on successful completion
    - Rolls back transactions on exceptions
    - Closes the session to return connection to pool
    - Retries connection on temporary failures
    
    Yields:
        Session: SQLModel database session
        
    Raises:
        OperationalError: After max retries for connection issues
        Exception: For other database errors
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
            # Exponential backoff before retry
            import time
            time.sleep(0.5 * retry_count)
        except Exception as e:
            logger.error(f"Unexpected database error: {e}")
            raise


def check_db_connection():
    """
    Test database connectivity for health checks.
    
    Performs a simple SELECT query to verify the database is reachable
    and responding. Used by the health check endpoint.
    
    Returns:
        bool: True if connection successful, False otherwise
        
    Raises:
        Exception: Re-raises exceptions for health check endpoint to handle
    """
    try:
        with Session(engine) as session:
            # Simple query to verify database connectivity
            session.exec(text("SELECT 1"))
            return True
    except OperationalError as e:
        logger.error(f"Database connection failed: {e}")
        raise  # Let health check endpoint handle the error
    except Exception as e:
        logger.error(f"Unexpected database error: {e}")
        raise


def get_session_with_retry(max_retries: int = 3):
    """
    Alternative session dependency with configurable retry count.
    
    Provides the same functionality as get_session but allows customizing
    the number of retry attempts for specific use cases.
    
    Args:
        max_retries: Maximum number of connection retry attempts
        
    Yields:
        Session: SQLModel database session
        
    Note:
        This function is currently identical to get_session.
        Consider using get_session directly unless custom retry logic is needed.
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
            # Exponential backoff before retry
            import time
            time.sleep(0.5 * retry_count)
        except Exception as e:
            logger.error(f"Unexpected database error: {e}")
            raise
