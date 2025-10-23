"""
This module initializes and configures the FastAPI application by registering all feature routers.
It centralizes the inclusion of routers for different parts of the API (authentication, user management),
keeping the application setup organized and maintainable.
"""

from fastapi import FastAPI

from features.auth.controller import router as auth_router
from features.conversations.controller import router as conversations_router
from features.generate.controller import router as generate_router
from features.image_storage.controller import router as upload_image_router
from features.llm_providers.controller import router as llm_providers_router
from features.messages.controller import router as messages_router
from features.user_memes.controller import router as user_memes_router
from features.users.controller import router as user_router


def register_routers(app: FastAPI):
    """
    Register all API routers to the provided FastAPI app instance.
    This function ensures that the authentication and user feature routers are included,
    enabling endpoint groups for login, signup, profile management, and other user operations.
    """
    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(upload_image_router)
    app.include_router(user_memes_router)
    app.include_router(generate_router)
    app.include_router(llm_providers_router)
    app.include_router(conversations_router)
    app.include_router(messages_router)
