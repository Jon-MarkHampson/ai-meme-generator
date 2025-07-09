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


def get_current_user_with_refresh(
    token: str = Depends(get_token_from_cookie_or_header),
    session: Session = Depends(get_session),
) -> tuple[User, str | None]:
    """
    Returns the authenticated User instance and a new token if refresh is needed.
    This version checks if the token is close to expiry and generates a new one.
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

        # Check if token expires within 30 minutes
        exp = payload.get("exp")
        if exp:
            current_time = datetime.now(timezone.utc).timestamp()
            time_until_expiry = exp - current_time

            # If less than 30 minutes remaining, create a new token
            if time_until_expiry < 1800:  # 30 minutes in seconds
                new_token = create_access_token(
                    subject=user_id,
                    expires_delta=timedelta(
                        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
                    ),
                )
                logger.info(
                    "Refreshing token for user %s, %d seconds remaining",
                    user_id,
                    time_until_expiry,
                )
            else:
                new_token = None
        else:
            new_token = None

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
    return user, new_token
