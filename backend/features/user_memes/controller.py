import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from database.core import get_session
from entities.user import User
from features.auth.service import get_current_user
from .models import UserMemeCreate, UserMemeRead, UserMemeUpdate, UserMemeList
from .service import (
    create_user_meme as service_create,
    read_user_meme as service_read,
    update_user_meme as service_update,
    delete_user_meme as service_delete,
    list_user_memes as service_list,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/user_memes", tags=["user_memes"])


@router.post(
    "/",
    response_model=UserMemeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user meme.",
)
def create_user_meme(
    data: UserMemeCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UserMemeRead:
    return service_create(data, session, current_user)


@router.get(
    "/{meme_id}",
    response_model=UserMemeRead,
    summary="Get a user meme by ID.",
)
def get_user_meme(
    meme_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UserMemeRead:
    return service_read(session, current_user, meme_id)


@router.patch(
    "/{meme_id}",
    response_model=UserMemeRead,
    summary="Update a user meme by ID.",
)
def update_user_meme(
    meme_id: str,
    data: UserMemeUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UserMemeRead:
    return service_update(meme_id, data, session, current_user)


@router.delete(
    "/{meme_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user meme by ID.",
)
def delete_user_meme(
    meme_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    service_delete(meme_id, session, current_user)


@router.get(
    "/",
    response_model=UserMemeList,
    summary="List all user memes.",
)
def list_user_memes(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UserMemeList:
    return service_list(session, current_user)
