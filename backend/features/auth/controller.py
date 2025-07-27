# backend/features/auth/controller.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from config import settings
from database.core import get_session
from entities.user import User
from ..users.models import UserCreate, UserRead
from .service import (
    create_user_account,
    authenticate_user,
    create_session_token,
    refresh_user_session,
    get_current_user,
    validate_session_status,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup")
def signup(
    user_in: UserCreate,
    session: Session = Depends(get_session),
):
    """
    Create a new user account and log them in.
    """
    # Create user account
    user = create_user_account(user_in, session)

    # Create session token
    access_token = create_session_token(user.id)

    # Set cookie and return user info
    response = JSONResponse(
        content={
            "user": UserRead.from_orm(user).dict(),
            "message": "Account created successfully",
        }
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # Change to: secure=settings.ENVIRONMENT == "production"
        samesite="lax",  # Changed from "strict" to "lax" for cross-origin
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    return response


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    """
    Authenticate user and create session.
    """
    # Authenticate user
    user = authenticate_user(form_data.username, form_data.password, session)

    # Create session token
    access_token = create_session_token(user.id)

    # DEBUG: Log the created token
    print(
        f"DEBUG: Created token: {access_token[:20]}..."
        if access_token
        else "DEBUG: No token created!"
    )

    # Set cookie
    response = JSONResponse(content={"message": "Login successful"})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # Change to: secure=settings.ENVIRONMENT == "production"
        samesite="lax",  # Changed from "strict" to "lax"
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    # DEBUG: Log the response headers
    print(f"DEBUG: Response cookies: {response.headers}")
    return response


@router.post("/refresh")
def refresh_session(
    current_user: User = Depends(get_current_user),
):
    """
    Refresh the user's session.
    """
    # Create new token
    access_token = refresh_user_session(current_user.id)

    # Update cookie
    response = JSONResponse(content={"message": "Session refreshed successfully"})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # Change to: secure=settings.ENVIRONMENT == "production"
        samesite=None,  # Changed from "strict" to "lax" - Now change to None for testing!
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    return response


@router.post("/logout")
def logout():
    """
    Clear the session cookie.
    """
    response = JSONResponse(content={"message": "Logged out successfully"})
    response.delete_cookie("access_token", path="/")
    return response


@router.get("/session-status")
def get_session_status(
    current_user: User = Depends(get_current_user),
):
    """
    Get current session status and time remaining.
    """
    return validate_session_status(current_user.id)
