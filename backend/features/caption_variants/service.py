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
    # Extract the caption_request_id from the payload
    payload = data.model_dump()
    request_id = payload["request_id"]

    if not request_id:
        logger.warning(
            f"User {current_user.id} attempted to create CaptionVariant without request ID"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Request ID is required"
        )
    # Ensure the request_id exists in CaptionRequest
    statement = select(CaptionRequest).where(
        CaptionRequest.id == request_id, CaptionRequest.user_id == current_user.id
    )
    if not session.exec(statement).first():
        logger.warning(
            f"User {current_user.id} attempted to create CaptionVariant with non-existent CaptionRequest {request_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CaptionRequest {request_id!r} not found",
        )
    # Create the CaptionVariant object
    variant = CaptionVariant(**payload)

    if not variant.caption_text:
        logger.warning(
            f"User {current_user.id} attempted to create CaptionVariant without caption text"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Caption text is required"
        )

    if variant.variant_rank < 0:
        logger.warning(
            f"User {current_user.id} attempted to create CaptionVariant with negative variant rank"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Variant rank must be non-negative",
        )

    if not variant.request_id:
        logger.warning(
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
        logger.warning(
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
        logger.warning(f"CaptionVariant {variant_id} not found")
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
        logger.warning(f"CaptionVariant {variant_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    session.delete(variant)
    session.commit()

    logger.info(f"CaptionVariant {variant.id} deleted by User {current_user.id}")
    return None


def list_caption_variants(
    session: Session,
    current_user: User,
) -> CaptionVariantList:
    variants = session.exec(
        select(CaptionVariant)
        .join(CaptionRequest, CaptionVariant.request_id == CaptionRequest.id)
        .where(CaptionRequest.user_id == current_user.id)
    ).all()

    logger.info(f"Listing {len(variants)} caption variants for User {current_user.id}")
    return CaptionVariantList(variants=variants)
