import logging
from fastapi import HTTPException, status
from sqlmodel import Session

from entities.user import User
from .models import UserUpdate, UserDelete
from features.auth.service import get_password_hash, pwd_context


logger = logging.getLogger(__name__)


def read_current_user(current_user: User) -> User:
    """
    Simply return the current_user ORM object. The controller will let FastAPI
    apply `response_model=UserRead` and convert to Pydantic for us.
    """
    return current_user


def update_current_user(
    user_update: UserUpdate,
    session: Session,
    current_user: User,
) -> User:
    """
    Take only the fields provided in user_update (exclude unset),
    re-hash the password if present, then commit+refresh the ORM object.
    Return the updated ORM User.
    """
    data = user_update.model_dump(exclude_unset=True)

    # 1) Pull out and verify `current_password`:
    supplied_old_pw = data.pop("current_password", None)

    # (always non‐None because Pydantic demands it)
    if not pwd_context.verify(supplied_old_pw, current_user.hashed_password):
        logger.exception(
            f"User {current_user.id} attempted to update profile with incorrect password."
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect.",
        )
    logger.info(f"User {current_user.id} verified their current password successfully.")

    # 2) If the client sent a new `password`, hash+store it:
    if "password" in data:
        new_pw = data.pop("password")
        current_user.hashed_password = get_password_hash(new_pw)
        logger.info(f"User {current_user.id} updated their password successfully.")

    # 3) Update first_name/last_name/email if present:
    if "first_name" in data:
        current_user.first_name = data["first_name"]
        logger.info(f"User {current_user.id} updated their first name successfully.")
    if "last_name" in data:
        current_user.last_name = data["last_name"]
        logger.info(f"User {current_user.id} updated their last name successfully.")
    if "email" in data:
        current_user.email = data["email"]
        logger.info(f"User {current_user.id} updated their email successfully.")
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user


def delete_current_user(
    delete_in: UserDelete,
    session: Session,
    current_user: User,
) -> None:
    """
    Verify that delete_in.password matches current_user.hashed_password.
    If not, raise 401. If it matches, delete and commit.
    """
    if not pwd_context.verify(delete_in.password, current_user.hashed_password):
        logger.exception(
            f"User {current_user.id} attempted to delete account with incorrect password."
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password, cannot delete account.",
        )
    logger.info(f"User {current_user.id} is deleting their account.")
    session.delete(current_user)
    session.commit()
    # Return None; controller will return a 204 No Content automatically.
    return None
