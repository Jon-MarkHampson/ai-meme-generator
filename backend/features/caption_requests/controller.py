import logging
from fastapi import APIRouter, Depends, status, HTTPException
from sqlmodel import Session
from database.core import get_session
from entities.user import User
from features.auth.service import get_current_user
from .models import (
    CaptionRequestCreate,
    CaptionRequestRead,
    CaptionRequestUpdate,
    CaptionRequestDelete,
    CaptionRequestList,
)
from .service import (
    create_caption_request as service_create,
    read_caption_request as service_read,
    update_caption_request as service_update,
    delete_caption_request as service_delete,
    list_caption_requests as service_list,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/caption_requests", tags=["caption_requests"])


@router.post(
    "/",
    response_model=CaptionRequestRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new caption request.",
)
def create_caption_request(
    payload: CaptionRequestCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CaptionRequestRead:
    return service_create(payload, session, current_user)


@router.get(
    "/{request_id}",
    response_model=CaptionRequestRead,
    summary="Get a caption request by ID.",
)
def get_caption_request(
    request_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CaptionRequestRead:
    return service_read(request_id, session, current_user)


@router.patch(
    "/{request_id}",
    response_model=CaptionRequestRead,
    summary="Update a caption request by ID.",
)
def update_caption_request(
    request_id: str,
    payload: CaptionRequestUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CaptionRequestRead:
    return service_update(request_id, payload, session, current_user)


@router.delete(
    "/{request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a caption request by ID.",
)
def delete_caption_request(
    request_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    # will 404 or 403 if bad, else just delete and return 204
    service_delete(request_id, session, current_user)


@router.get(
    "/",
    response_model=CaptionRequestList,
    summary="List all caption requests for the current user.",
)
def list_caption_requests(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CaptionRequestList:
    return service_list(session, current_user)
