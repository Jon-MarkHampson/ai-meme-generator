import logging
from fastapi import APIRouter, Depends, status
from sqlmodel import Session
from database.core import get_session
from entities.user import User
from features.auth.service import get_current_user
from .models import ImageVariantCreate, ImageVariantRead, ImageVariantList
from .service import (
    create_image_variant as service_create,
    read_image_variant as service_read,
    delete_image_variant as service_delete,
    list_image_variants as service_list,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/image_variants", tags=["image_variants"])


@router.post(
    "/",
    response_model=ImageVariantRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new image variant.",
)
def create_image_variant(
    payload: ImageVariantCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ImageVariantRead:
    return service_create(payload, session, current_user)


@router.get(
    "/{variant_id}",
    response_model=ImageVariantRead,
    summary="Get an image variant by ID.",
)
def get_image_variant(
    variant_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ImageVariantRead:
    return service_read(variant_id, session, current_user)


@router.delete(
    "/{variant_id}",
    status_code=204,
    summary="Delete an image variant by ID.",
)
def delete_image_variant(
    variant_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    service_delete(variant_id, session, current_user)


@router.get(
    "/",
    response_model=ImageVariantList,
    summary="List all image variants.",
)
def list_image_variants(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ImageVariantList:
    return service_list(session, current_user)
