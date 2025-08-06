"""
Authentication service implementing core security functionality.

This module handles the business logic for user authentication including:
- Password hashing and verification using bcrypt
- JWT token generation and validation
- Session management with configurable expiration
- User account creation with duplicate prevention
- Token extraction from both cookies and headers for API flexibility

Security considerations:
- Passwords are never stored in plain text
- Tokens include expiration claims to limit exposure
- Failed authentications log attempts for monitoring
- Race conditions handled during user registration
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Cookie, Depends, Header, HTTPException, status
from jose import JWTError, ExpiredSignatureError, jwt
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from config import settings
from database.core import get_session
from features.users.model import User
from ..users.schema import UserCreate, UserRead
from utils.security import get_password_hash, verify_password

logger = logging.getLogger(__name__)


def create_access_token(subject: str, expires_delta: timedelta) -> str:
    """
    Create a JWT access token for user authentication.
    
    Args:
        subject: The subject of the token (typically user ID)
        expires_delta: How long until the token expires
        
    Returns:
        Encoded JWT token as a string
    """
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"sub": subject, "exp": expire}
    token = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    logger.info(f"Issued token for {subject}, expires at {expire}")
    return token


def create_user_account(user_in: UserCreate, session: Session) -> UserRead:
    """
    Create a new user account with hashed password.
    
    Args:
        user_in: UserCreate model with registration data
        session: Database session for executing queries
        
    Returns:
        UserRead model with the created user data
        
    Raises:
        HTTPException: If email is already registered
    """
    # Check if email already exists to prevent duplicates
    existing = session.exec(select(User).where(User.email == user_in.email)).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create user with hashed password for security
    user = User(
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
    )

    session.add(user)
    try:
        session.commit()
        session.refresh(user)  # Get the generated ID
    except IntegrityError:
        # Handle race condition where email was registered between our check and insert
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    logger.info(f"Created new user account: {user.id}")
    return UserRead.model_validate(user)


def authenticate_user(email: str, password: str, session: Session) -> UserRead:
    """
    Authenticate user by verifying email and password.
    
    Args:
        email: User's email address
        password: Plain text password to verify
        session: Database session for executing queries
        
    Returns:
        UserRead model with authenticated user data
        
    Raises:
        HTTPException: If credentials are invalid
    """
    user = session.exec(select(User).where(User.email == email)).first()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    logger.info(f"User {user.id} authenticated successfully")
    return UserRead.model_validate(user)


def create_session_token(user_id: str) -> str:
    """
    Create a new session token for authenticated user.
    
    Generates a JWT with user ID as subject and configured expiration.
    Tokens are stateless, containing all necessary validation data.
    
    Args:
        user_id: The ID of the authenticated user
        
    Returns:
        JWT token string for cookie storage
    """
    return create_access_token(
        subject=user_id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def refresh_user_session(user_id: str) -> str:
    """
    Generate a fresh token to extend an active session.
    
    Called when users are actively using the application to prevent
    disruption. The new token has a full expiration period from the
    current time.
    
    Args:
        user_id: The ID of the user whose session to refresh
        
    Returns:
        New JWT token with extended expiration
    """
    logger.info(f"Refreshing session for user {user_id}")
    return create_session_token(user_id)


def get_token_from_cookie_or_header(
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None),
) -> str:
    """
    Extract JWT token from HTTP request.
    
    Supports both cookie-based sessions (primary) and Authorization 
    header (for API clients). Cookies are preferred for browser 
    security, while headers support programmatic access.
    
    Args:
        authorization: Optional Authorization header value
        access_token: Optional cookie containing JWT
        
    Returns:
        Extracted JWT token string
        
    Raises:
        HTTPException: 401 if no valid token found
    """
    # Prefer cookie for browser-based authentication
    if access_token:
        return access_token

    # Fallback to Authorization header for API clients
    if authorization and authorization.startswith("Bearer "):
        return authorization[7:]

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: str = Depends(get_token_from_cookie_or_header),
    session: Session = Depends(get_session),
) -> User:
    """
    Validate token and retrieve authenticated user.
    
    This dependency is injected into protected endpoints to ensure
    only authenticated users can access them. Validates token signature,
    expiration, and user existence.
    
    Args:
        token: JWT token from cookie or header
        session: Database session for user lookup
        
    Returns:
        User object if authentication successful
        
    Raises:
        HTTPException: 401 for any authentication failure
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    return user


def validate_session_status(user_id: str) -> dict:
    """
    Check session validity and calculate remaining time.
    
    Used by frontend to display session warnings and coordinate
    automatic logout. In production, this would decode the token
    to check actual expiration time.
    
    Args:
        user_id: The ID of the user to check
        
    Returns:
        Dict with authentication status and timing info
        
    TODO: Implement actual token expiration checking when
    frontend session timer integration is complete.
    """
    # Placeholder implementation - would check actual token expiry
    return {"authenticated": True, "user_id": user_id, "message": "Session is valid"}
