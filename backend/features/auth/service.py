import logging
from datetime import datetime, timedelta, timezone

from fastapi import Cookie, Depends, Header, HTTPException, status
from jose import JWTError, ExpiredSignatureError, jwt
from passlib.context import CryptContext
from sqlmodel import Session

from config import settings
from database.core import get_session
from entities.user import User
from .models import TokenData

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plaintext password against its hashed counterpart.
    Returns True if they match, False otherwise.
    """
    return pwd_context.verify(plain, hashed)


def get_password_hash(password: str) -> str:
    """
    Hash a plaintext password using bcrypt.
    Returns the resulting hash.
    """
    return pwd_context.hash(password)


def create_access_token(
    subject: str,
    expires_delta: timedelta,
) -> str:
    """
    Create a JWT access token for a given subject (user ID), with the specified expiration delta.
    Embeds 'sub' and 'exp' claims, signs with our secret, and returns the token string.
    """
    to_encode = {"sub": subject}
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode["exp"] = expire
    token = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    logger.info("Issued token for %s, expires at %s", subject, expire)
    return token


def get_token_from_cookie_or_header(
    authorization: str | None = Header(None),
    access_token: str | None = Cookie(None),
) -> str:
    # 1) Try cookie first
    if access_token:
        return access_token
    # 2) Fallback to header
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
    Returns the authenticated User instance.
    """
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id: str = payload.get("sub")
        if not user_id:
            raise credentials_exc
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise credentials_exc

    user = session.get(User, user_id)
    if not user:
        raise credentials_exc

    logger.info("Authenticated user %s", user.id)
    return user
