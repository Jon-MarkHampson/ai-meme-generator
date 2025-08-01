"""
Authentication controller handling user registration and session management.

This module provides HTTP endpoints for user authentication workflows including:
- User registration with immediate session creation
- Login with JWT-based session tokens
- Session refresh to extend active sessions
- Logout with proper cookie cleanup
- Session status validation for frontend timers

All endpoints follow RESTful conventions and use HTTP-only cookies for 
secure token storage, preventing XSS attacks while maintaining usability.
"""
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
    Register a new user and establish their session.
    
    Args:
        user_in: Registration data (email, password, names)
        session: Database session from dependency injection
        
    Returns:
        JSON response with user data and sets HTTP-only cookie
    """
    user = create_user_account(user_in, session)
    access_token = create_session_token(user.id)
    
    response = JSONResponse(
        content={
            "user": UserRead.model_validate(user).model_dump(),
            "message": "Account created successfully",
        }
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.ENVIRONMENT
        == "production",  # False for development, True for production
        samesite="lax",  # Allows cross-origin cookies for development
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
    Authenticate user credentials and establish a new session.
    
    Uses OAuth2 password flow for compatibility with standard authentication
    libraries while maintaining security through HTTP-only cookies.
    
    Args:
        form_data: OAuth2 form containing username (email) and password
        session: Database session from dependency injection
        
    Returns:
        JSON response confirming login with HTTP-only session cookie
        
    Raises:
        HTTPException: 401 if credentials are invalid
    """
    # Authenticate user
    user = authenticate_user(form_data.username, form_data.password, session)

    # Create session token
    access_token = create_session_token(user.id)

    # Create response with session cookie
    response = JSONResponse(content={"message": "Login successful"})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.ENVIRONMENT
        == "production",  # False for development, True for production
        samesite="lax",  # Allows cross-origin cookies for development
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    return response


@router.post("/refresh")
def refresh_session(
    current_user: User = Depends(get_current_user),
):
    """
    Extend an active session before expiration.
    
    Called by frontend session management when approaching timeout.
    Generates a new token with fresh expiration while maintaining
    the same user context.
    
    Args:
        current_user: Authenticated user from token validation
        
    Returns:
        JSON response with refreshed session cookie
        
    Note:
        Frontend should call this before the warning timer expires
        to prevent session interruption during active use.
    """
    # Generate fresh token with extended expiration
    access_token = refresh_user_session(current_user.id)

    # Replace existing cookie with new token
    response = JSONResponse(content={"message": "Session refreshed successfully"})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.ENVIRONMENT
        == "production",  # False for development, True for production
        samesite="lax",  # Allows cross-origin cookies for development
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    return response


@router.post("/logout")
def logout():
    """
    Terminate user session and clear authentication.
    
    Removes the HTTP-only session cookie, effectively logging out
    the user. No server-side session invalidation needed as JWTs
    are stateless.
    
    Returns:
        JSON response confirming logout with cookie deletion
    """
    response = JSONResponse(content={"message": "Logged out successfully"})
    response.delete_cookie("access_token", path="/")
    return response


@router.get("/session-status")
def get_session_status(
    current_user: User = Depends(get_current_user),
):
    """
    Validate session and return timing information.
    
    Used by frontend to synchronize session timers and display
    warnings before automatic logout. Provides millisecond precision
    for accurate countdown displays.
    
    Args:
        current_user: Authenticated user from token validation
        
    Returns:
        Dict containing:
        - is_valid: Whether session is still active
        - time_remaining_ms: Milliseconds until expiration
        - expires_at: ISO timestamp of expiration
    """
    return validate_session_status(current_user.id)
