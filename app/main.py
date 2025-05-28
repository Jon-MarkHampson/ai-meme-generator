from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.db.database import create_db_and_tables
from app.routers import hero


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    create_db_and_tables()
    yield
    # Shutdown: nothing (yet)


app = FastAPI(lifespan=lifespan)

app.include_router(hero.router)


@app.get("/")
def read_root():
    return {"message": "Hello from app/main.py!"}
