import logging
from fastapi import HTTPException, status
from sqlmodel import Session, select
from entities.image_variants import ImageVariant
from entities.caption_variants import CaptionVariant
from entities.caption_requests import CaptionRequest
from entities.user import User
from .models import (
    ImageVariantCreate,
    ImageVariantRead,
    ImageVariantList,
)

logger = logging.getLogger(__name__)


def create_image_variant(
    data: ImageVariantCreate,
    session: Session,
    current_user: User,
) -> ImageVariantRead:
    # Extract the caption_variant_id from the payload
    payload = data.model_dump()
    caption_variant_id = payload["caption_variant_id"]

    # Verify that the caption_variant_id is provided
    if not caption_variant_id:
        logger.warning(
            f"User {current_user.id} attempted to create ImageVariant without caption variant ID"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Caption variant ID is required",
        )
    # Ensure the caption_variant_id exists in CaptionVariant
    statement = (
        select(CaptionVariant)
        # Join from CaptionVariant to CaptionRequest
        .join(CaptionRequest, CaptionVariant.request_id == CaptionRequest.id).where(
            CaptionVariant.id == caption_variant_id,
            CaptionRequest.user_id == current_user.id,
        )
    )
    if not session.exec(statement).first():
        logger.warning(
            f"User {current_user.id} attempted to create ImageVariant with non-existent CaptionVariant {caption_variant_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CaptionVariant {caption_variant_id!r} not found",
        )
    # Create the ImageVariant object
    variant = ImageVariant(**payload)

    # Validate all required fields
    if not variant.image_url:
        logger.warning(
            f"User {current_user.id} attempted to create ImageVariant without image URL"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Image URL is required"
        )

    if variant.variant_rank < 0:
        logger.warning(
            f"User {current_user.id} attempted to create ImageVariant with negative variant rank"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Variant rank must be a non-negative integer",
        )

    session.add(variant)
    session.commit()
    session.refresh(variant)

    logger.info(f"ImageVariant {variant.id} created by User {current_user.id}")
    return variant


def read_image_variant(
    variant_id: str,
    session: Session,
    current_user: User,
) -> ImageVariantRead:
    statement = (
        select(ImageVariant)
        # join from ImageVariant -> CaptionVariant
        .join(CaptionVariant, ImageVariant.caption_variant_id == CaptionVariant.id)
        # then join from CaptionVariant -> CaptionRequest
        .join(CaptionRequest, CaptionVariant.request_id == CaptionRequest.id)
        # only keep those where the request belongs to the current user
        .where(ImageVariant.id == variant_id, CaptionRequest.user_id == current_user.id)
    )
    variant = session.exec(statement).one_or_none()

    if not variant:
        logger.warning(
            f"User {current_user.id} attempted to read non-existent ImageVariant {variant_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image variant not found"
        )
    logger.info(f"ImageVariant {variant.id} read by User {current_user.id}")
    return variant


def delete_image_variant(
    variant_id: str,
    session: Session,
    current_user: User,
) -> None:
    statement = (
        select(ImageVariant)
        # join from ImageVariant -> CaptionVariant
        .join(CaptionVariant, ImageVariant.caption_variant_id == CaptionVariant.id)
        # then join from CaptionVariant -> CaptionRequest
        .join(CaptionRequest, CaptionVariant.request_id == CaptionRequest.id)
        # only keep those where the request belongs to the current user
        .where(ImageVariant.id == variant_id, CaptionRequest.user_id == current_user.id)
    )
    variant = session.exec(statement).one_or_none()

    if not variant:
        logger.warning(
            f"User {current_user.id} attempted to delete non-existent ImageVariant {variant_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image variant not found"
        )

    session.delete(variant)
    session.commit()
    logger.info(f"ImageVariant {variant.id} deleted by User {current_user.id}")


def list_image_variants(
    session: Session,
    current_user: User,
) -> ImageVariantList:
    statement = (
        select(ImageVariant)
        # join from ImageVariant -> CaptionVariant
        .join(CaptionVariant, ImageVariant.caption_variant_id == CaptionVariant.id)
        # then join from CaptionVariant -> CaptionRequest
        .join(CaptionRequest, CaptionVariant.request_id == CaptionRequest.id)
        # only keep those where the request belongs to the current user
        .where(CaptionRequest.user_id == current_user.id)
    )
    variants = session.exec(statement).all()

    if not variants:
        logger.info(f"No image variants found for User {current_user.id}")
        return ImageVariantList(variants=[])

    logger.info(f"Listed {len(variants)} image variants for User {current_user.id}")
    return ImageVariantList(variants=variants)
