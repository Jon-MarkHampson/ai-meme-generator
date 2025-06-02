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

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")  # points at auth router


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against its hashed version."""
    return pwd_context.verify(plain, hashed)


def get_password_hash(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(password)


def create_access_token(
    subject: str,
    expires_delta: timedelta,
) -> str:
    """Create a JWT access token for a subject with expiration."""
    to_encode = {"sub": str(subject)}
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
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
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        subject = payload.get("sub")
        if subject is None:
            raise credentials_exc
        token_data = TokenData(user_id=subject)
    except ExpiredSignatureError:
        # token was valid but expired
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (JWTError, ValueError):
        # invalid token
        raise credentials_exc

    user = session.get(User, token_data.user_id)
    if not user:
        raise credentials_exc
    return user
