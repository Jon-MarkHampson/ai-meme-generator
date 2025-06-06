import logging
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, ExpiredSignatureError, jwt
from passlib.context import CryptContext
from sqlmodel import Session

from config import settings
from database.core import get_session
from entities.user import User
from .models import Token, TokenData

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")  # points at auth router


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against its hashed version."""
    logger.debug("Verifying password against hash")
    is_valid = pwd_context.verify(plain, hashed)
    logger.debug("Password verification result: %s", is_valid)
    return is_valid


def get_password_hash(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    logger.debug("Hashing password")
    hashed = pwd_context.hash(password)
    logger.debug("Generated password hash")
    return hashed


def create_access_token(
    subject: str,
    expires_delta: timedelta,
) -> str:
    """Create a JWT access token for a subject with expiration."""
    logger.debug(
        "Creating access token for subject=%s with expires_delta=%s",
        subject,
        expires_delta,
    )
    to_encode = {"sub": subject}
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    logger.debug("Token payload prepared: %s", to_encode)
    token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    logger.info("Access token created for subject=%s, expires at=%s", subject, expire)
    return token
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)
) -> User:
    """Extract and return the current user from the JWT token, or raise HTTP 401."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        logger.debug("Decoding JWT token for authentication")
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        logger.debug("Token decoded successfully: %s", payload)

        subject = payload.get("sub")
        if subject is None:
            logger.error("JWT payload missing 'sub' claim")
            raise credentials_exc

        token_data = TokenData(user_id=subject)

    except ExpiredSignatureError:
        logger.warning("JWT token has expired: %s", token)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (JWTError, ValueError) as e:
        logger.error("Error decoding JWT token: %s", e)
        raise credentials_exc

    user = session.get(User, token_data.user_id)
    if not user:
        logger.error("User not found for id: %s", token_data.user_id)
        raise credentials_exc

    logger.info("Authenticated user %s", user.id)
    return user
