from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from database.core import create_db_and_tables
from api import register_routers


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    create_db_and_tables()
    yield
    # Shutdown: nothing (yet)


app = FastAPI(lifespan=lifespan)


# Health check at root URL
@app.get("/", summary="Health check")
async def health_check():
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
