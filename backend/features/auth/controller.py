from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from datetime import timedelta

from .models import Token, SignupResponse
from ..users.models import UserCreate
from entities.user import User
from .service import verify_password, get_password_hash, create_access_token
from database.core import get_session
from config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=SignupResponse)
def signup(
    user_in: UserCreate,
    session: Session = Depends(get_session),
):
    # 1) Check if a user with this email already exists
    existing = session.exec(
        select(User).where(User.email == user_in.email)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # 2) Hash the password and create the new User
    hashed = get_password_hash(user_in.password)
    user = User(
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        email=user_in.email,
        hashed_password=hashed
    )

    session.add(user)
    try:
        session.commit()
        session.refresh(user)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered."
        )

    # 3) Generate a JWT for the new user
    access_token = create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    # 4) Return both the newly minted user data and the token
    return SignupResponse(
        user=user,
        access_token=access_token,
        token_type="bearer"
    )


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    """
    Authenticate using email + password (FastAPI’s OAuth2 form still calls it “username”,
    so we treat form_data.username as the user’s email). Return a JWT if valid.
    """
    # 1) Look up user by email
    user = session.exec(
        select(User).where(User.email == form_data.username)
    ).first()

    # 2) Verify password
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # 3) Create a new JWT
    access_token = create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    # 4) Return it
    return {"access_token": access_token, "token_type": "bearer"}