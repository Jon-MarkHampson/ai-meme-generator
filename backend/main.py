import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from logging_config import configure_logging, LogLevels
from database.core import create_db_and_tables
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


# Health check at root URL
@app.get("/", summary="Health check")
async def health_check():
    logger.info("Health check endpoint called")
    return {"Health Check - status": "ok"}


origins = [
    "http://localhost:3000"
]  # Add additional allowed origins here, such as the production frontend URL

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_routers(app)
logger.info("Routers registered and application setup complete")
