"""
This module initializes and configures the FastAPI application by registering all feature routers.
It centralizes the inclusion of routers for different parts of the API (authentication, user management),
keeping the application setup organized and maintainable.
"""

from fastapi import FastAPI

from features.auth.controller import router as auth_router
from features.users.controller import router as user_router
from features.upload_image.controller import router as upload_image_router
from features.caption_requests.controller import router as caption_requests_router
from features.caption_variants.controller import router as caption_variants_router


def register_routers(app: FastAPI):
    """
    Register all API routers to the provided FastAPI app instance.
    This function ensures that the authentication and user feature routers are included,
    enabling endpoint groups for login, signup, profile management, and other user operations.
    """
    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(upload_image_router)
    app.include_router(caption_requests_router)
    app.include_router(caption_variants_router)
