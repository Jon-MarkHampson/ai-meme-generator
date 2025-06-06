import logging
from fastapi import APIRouter, Depends, Body, status
from sqlmodel import Session

from database.core import get_session
from entities.user import User
from features.auth.service import get_current_user
from .models import UserUpdate, UserRead, DeleteRequest
from .service import (
    read_current_user,
    update_current_user,
    delete_current_user,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserRead,
    summary="Return the currently authenticated user.",
)
def read_me(
    current_user: User = Depends(get_current_user),
):
    """
    Controller for GET /users/me
    Simply calls the service to fetch “current_user” and returns it.
    """
    logger.info(f"GET /users/me - user_id={current_user.id}")
    return read_current_user(current_user)


@router.patch(
    "/me",
    response_model=UserRead,
    summary="Update current user's profile fields and return the updated user.",
)
def update_me(
    user_update: UserUpdate = Body(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Controller for PATCH /users/me
    Delegates to service.update_current_user(...)
    """
    logger.info(
        f"PATCH /users/me - user_id={current_user.id}, update={user_update.model_dump()}"
    )
    return update_current_user(
        user_update=user_update,
        session=session,
        current_user=current_user,
    )


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete current user account (requires password).",
)
def delete_me(
    delete_in: DeleteRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Controller for DELETE /users/me
    Delegates to service.delete_current_user(...). Returns 204 on success.
    """
    logger.info(f"DELETE /users/me - user_id={current_user.id}")
    delete_current_user(
        delete_in=delete_in,
        session=session,
        current_user=current_user,
    )
    return  # Returning None with 204 No Content
