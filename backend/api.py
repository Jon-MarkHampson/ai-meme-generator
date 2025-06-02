from fastapi import FastAPI

from features.auth.controller import router as auth_router
from features.users.controller import router as user_router

def register_routers(app: FastAPI):
    """
    Register all API routers.
    """
    app.include_router(auth_router)
    app.include_router(user_router)