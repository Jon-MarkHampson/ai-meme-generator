import logging
from fastapi import APIRouter, Depends, status
from sqlmodel import Session
from database.core import get_session
from entities.user import User
from features.auth.service import get_current_user
from .models import (
    CaptionVariantCreate,
    CaptionVariantRead,
    CaptionVariantList,
)
from .service import (
    create_caption_variant as service_create,
    read_caption_variant as service_read,
    delete_caption_variant as service_delete,
    list_caption_variants as service_list,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/caption_variants", tags=["caption_variants"])


@router.post(
    "/",
    response_model=CaptionVariantRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new caption variant.",
)
def create_caption_variant(
    payload: CaptionVariantCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CaptionVariantRead:
    return service_create(payload, session, current_user)


@router.get(
    "/{variant_id}",
    response_model=CaptionVariantRead,
    summary="Get a caption variant by ID.",
)
def get_caption_variant(
    variant_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CaptionVariantRead:
    return service_read(variant_id, session, current_user)


@router.delete(
    "/{variant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a caption variant by ID.",
)
def delete_caption_variant(
    variant_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    return service_delete(variant_id, session, current_user)


@router.get(
    "/",
    response_model=CaptionVariantList,
    summary="List all caption variants.",
)
def list_caption_variants(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CaptionVariantList:
    return service_list(session, current_user)
