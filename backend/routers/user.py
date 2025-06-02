from fastapi import APIRouter, Depends, Body, HTTPException, status
from sqlmodel import Session

from models.user import User
from schemas.user import UserUpdate, UserRead, DeleteRequest
from db.database import get_session
from config import settings
from auth.handler import get_current_user, get_password_hash, pwd_context


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user."""
    return current_user


@router.patch("/me", response_model=UserRead)
def update_me(
    user_update: UserUpdate = Body(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Update the current user's profile fields and return the updated user."""
    # Turn the Pydantic model into a dict of only the fields that were set
    data = user_update.model_dump(exclude_unset=True)
    # handle password separately if present
    if "password" in data:
        current_user.hashed_password = get_password_hash(data.pop("password"))
    for field, val in data.items():
        setattr(current_user, field, val)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete current user account (requires password)",
)
def delete_me(
    delete_in: DeleteRequest,                  # <-- only needs `password`
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Delete the current user's account, but only if the provided password is correct.
    """
    # Verify that the supplied password matches this user’s hashed password
    if not pwd_context.verify(delete_in.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password, cannot delete account.",
        )

    session.delete(current_user)
    session.commit()
    return  # 204 No Content
