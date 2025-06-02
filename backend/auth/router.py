from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from auth.handler import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
)
from config import settings
from db.database import get_session
from models.user import User
from schemas.user import UserCreate
from schemas.auth import Token, SignupResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=SignupResponse)
def signup(
    user_in: UserCreate,
    session: Session = Depends(get_session),
):
    # 1) Check if username already exists
    exists = session.exec(
        select(User).where(User.username == user_in.username)
    ).first()
    if exists:
        # To avoid leaking which usernames exist, return a generic error
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # 2) Hash the password and create the User
    hashed = get_password_hash(user_in.password)
    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # 3) Generate a JWT for the new user
    access_token = create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    # 4) Return both user data and token
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
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    token = create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": token, "token_type": "bearer"}
