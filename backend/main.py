"""
Main FastAPI application entry point for the AI Meme Generator.
Handles app startup, database initialization, monitoring setup, and routing.
"""
import logging
import os
from contextlib import asynccontextmanager

import logfire
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import register_routers
from database.core import check_db_connection, create_db_and_tables
from logging_config import LogLevels, configure_logging

load_dotenv()


# Configure logging based on environment variable
raw_level = os.getenv("LOG_LEVEL", LogLevels.info)
configure_logging(raw_level)


# Reduce noise from third-party libraries in logs
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("hpack").setLevel(logging.WARNING)


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for startup and shutdown events.
    
    Args:
        app: FastAPI application instance
        
    Yields:
        None - allows app to run
    """
    logger.info("Application startup: creating database tables")
    create_db_and_tables()
    yield
    logger.info("Application shutdown: cleanup complete")


app = FastAPI(lifespan=lifespan)

# Configure Logfire monitoring and instrumentation
logfire.configure()
logfire.instrument_httpx()  # Monitor HTTP requests
logfire.instrument_pydantic_ai()  # Monitor AI agent interactions
logfire.instrument_fastapi(app, capture_headers=True)  # Monitor FastAPI requests


@app.get("/health/", summary="Health check")
async def health_check():
    """
    Basic health check endpoint to verify the API is running.
    
    Returns:
        Dict containing status information
    """
    logger.info("Health check endpoint called")
    return {"Health Check - status": "ok"}


@app.get("/health/db", summary="Database health check")
async def db_health_check():
    """
    Database connectivity health check endpoint.
    
    Returns:
        Dict containing database connection status
    """
    logger.info("Database health check endpoint called")
    try:
        check_db_connection()
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "error", "db": "not connected"}


# Configure CORS origins for frontend communication
# Using walrus operator to assign and use FRONTEND_URL in one line
origins = [
    FRONTEND_URL := os.getenv("FRONTEND_URL", "http://localhost:3000"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_routers(app)
logger.info("Routers registered and application setup complete")
