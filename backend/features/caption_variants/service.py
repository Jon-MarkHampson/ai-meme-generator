import logging
from fastapi import HTTPException, status
from sqlmodel import Session, select
from entities.caption_variants import CaptionVariant
from entities.caption_requests import CaptionRequest
from entities.user import User
from .models import (
    CaptionVariantCreate,
    CaptionVariantRead,
    CaptionVariantList,
)

logger = logging.getLogger(__name__)


def create_caption_variant(
    data: CaptionVariantCreate,
    session: Session,
    current_user: User,
) -> CaptionVariantRead:
    variant = CaptionVariant(**data.model_dump(), user_id=current_user.id)

    if not variant.caption_text:
        logger.exception(
            f"User {current_user.id} attempted to create CaptionVariant without caption text"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Caption text is required"
        )

    if variant.variant_rank < 0:
        logger.exception(
            f"User {current_user.id} attempted to create CaptionVariant with negative variant rank"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Variant rank must be non-negative",
        )

    if not variant.request_id:
        logger.exception(
            f"User {current_user.id} attempted to create CaptionVariant without request ID"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Request ID is required"
        )
    # Check if the request_id exists in CaptionRequest

    request_exists = session.exec(
        select(CaptionRequest).where(CaptionRequest.id == variant.request_id)
    ).first()
    if not request_exists:
        logger.exception(
            f"CaptionRequest {variant.request_id} not found for CaptionVariant creation"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Caption request not found"
        )

    session.add(variant)
    session.commit()
    session.refresh(variant)

    logger.info(f"CaptionVariant {variant.id} created by User {current_user.id}")
    return variant


def read_caption_variant(
    variant_id: str,
    session: Session,
    current_user: User,
) -> CaptionVariantRead:
    statement = (
        select(CaptionVariant)
        .join(CaptionRequest, CaptionVariant.request_id == CaptionRequest.id)
        .where(
            CaptionVariant.id == variant_id,
            CaptionRequest.user_id == current_user.id,
        )
    )
    variant = session.exec(statement).one_or_none()
    if not variant:
        logger.exception(f"CaptionVariant {variant_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    logger.info(f"CaptionVariant {variant.id} read by User {current_user.id}")
    return CaptionVariantRead.model_validate(variant)


def delete_caption_variant(
    variant_id: str,
    session: Session,
    current_user: User,
) -> None:
    statement = (
        select(CaptionVariant)
        .join(CaptionRequest, CaptionVariant.request_id == CaptionRequest.id)
        .where(
            CaptionVariant.id == variant_id,
            CaptionRequest.user_id == current_user.id,
        )
    )
    variant = session.exec(statement).one_or_none()
    if not variant:
        logger.exception(f"CaptionVariant {variant_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    session.delete(variant)
    session.commit()

    logger.info(f"CaptionVariant {variant.id} deleted by User {current_user.id}")
    return None


def list_caption_variants(
    session: Session,
    current_user: User,
) -> CaptionVariantList:
    rows = session.exec(
        select(CaptionVariant)
        .join(CaptionRequest, CaptionVariant.request_id == CaptionRequest.id)
        .where(CaptionRequest.user_id == current_user.id)
    ).all()

    logger.info(f"Listing {len(rows)} caption variants for User {current_user.id}")
    return CaptionVariantList(variants=rows)
