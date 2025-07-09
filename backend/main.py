import os
import logging
import logfire
from dotenv import load_dotenv
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from logging_config import configure_logging, LogLevels
from database.core import create_db_and_tables, check_db_connection
from api import register_routers

load_dotenv()


# Read desired level from env (default to "INFO" if not provided)
raw_level = os.getenv("LOG_LEVEL", LogLevels.info)
configure_logging(raw_level)


logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("hpack").setLevel(logging.WARNING)


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup: creating database tables")
    create_db_and_tables()
    yield
    logger.info("Application shutdown: cleanup complete")


app = FastAPI(lifespan=lifespan)

# configure logfire
logfire.configure()
logfire.instrument_httpx()
logfire.instrument_pydantic()
logfire.instrument_pydantic_ai()
logfire.instrument_fastapi(app, capture_headers=True)
# logfire.instrument_psycopg(enable_commenter=True)


# Health check backend
@app.get("/health/", summary="Health check")
async def health_check():
    logger.info("Health check endpoint called")
    return {"Health Check - status": "ok"}


# Database health check
@app.get("/health/db", summary="Database health check")
async def db_health_check():
    logger.info("Database health check endpoint called")
    is_healthy = check_db_connection()
    if is_healthy:
        return {"Database Health Check - status": "ok"}
    else:
        return {
            "Database Health Check - status": "error",
            "message": "Database connection failed",
        }


# Default to localhost if not set
# Walrus operator to assign FRONTEND_URL and use it in CORS
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
