from fastapi import FastAPI
from contextlib import asynccontextmanager

from db.database import create_db_and_tables
from auth.router import router as auth_router
from routers import user


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    create_db_and_tables()
    yield
    # Shutdown: nothing (yet)


app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.include_router(user.router)
