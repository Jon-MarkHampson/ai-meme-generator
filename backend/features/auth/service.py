# backend/features/auth/service.py
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Cookie, Depends, Header, HTTPException, status
from jose import JWTError, ExpiredSignatureError, jwt
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from config import settings
from database.core import get_session
from entities.user import User
from ..users.models import UserCreate, UserRead
from utils.security import get_password_hash, verify_password

logger = logging.getLogger(__name__)


def create_access_token(subject: str, expires_delta: timedelta) -> str:
    """Create a JWT access token."""
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
    """Create a new user account."""
    # Check if email exists
    existing = session.exec(select(User).where(User.email == user_in.email)).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create user
    user = User(
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
    )

    session.add(user)
    try:
        session.commit()
        session.refresh(user)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    logger.info(f"Created new user account: {user.id}")
    return UserRead.model_validate(user)


def authenticate_user(email: str, password: str, session: Session) -> UserRead:
    """Authenticate user with email and password."""
    user = session.exec(select(User).where(User.email == email)).first()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    logger.info(f"User {user.id} authenticated successfully")
    return UserRead.model_validate(user)


def create_session_token(user_id: str) -> str:
    """Create a new session token for a user."""
    return create_access_token(
        subject=user_id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def refresh_user_session(user_id: str) -> str:
    """Refresh a user's session token."""
    logger.info(f"Refreshing session for user {user_id}")
    return create_session_token(user_id)


def get_token_from_cookie_or_header(
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None),
) -> str:
    """Extract token from cookie or Authorization header."""
    # Prefer cookie
    if access_token:
        return access_token

    # Fallback to header
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
    """Get the current authenticated user from token."""
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
    """Get session status and time remaining."""
    # This would typically check the token expiry
    # For now, return a simple status
    return {"authenticated": True, "user_id": user_id, "message": "Session is valid"}
