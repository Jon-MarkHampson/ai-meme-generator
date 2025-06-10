import logging
from fastapi import HTTPException, status
from sqlmodel import Session, select

from entities.caption_variants import CaptionVariant
from entities.caption_requests import CaptionRequest
from entities.user import User
from .models import CaptionVariantCreate, CaptionVariantRead, CaptionVariantList

logger = logging.getLogger(__name__)


def create_caption_variant(
    data: CaptionVariantCreate,
    session: Session,
    current_user: User,
) -> CaptionVariantRead:
    """
    Create a new CaptionVariant for one of the user's CaptionRequests.
    """
    # Verify the request belongs to this user
    exists = session.exec(
        select(CaptionRequest.id).where(
            CaptionRequest.id == data.request_id,
            CaptionRequest.user_id == current_user.id,
        )
    ).first()
    if not exists:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"CaptionRequest {data.request_id!r} not found",
        )

    variant = CaptionVariant(**data.model_dump())
    session.add(variant)
    session.commit()
    session.refresh(variant)

    logger.info("CaptionVariant %s created for Request %s", variant.id, data.request_id)
    return variant  # FastAPI will serialize via CaptionVariantRead


def read_caption_variant(
    variant_id: str,
    session: Session,
    current_user: User,
) -> CaptionVariantRead:
    """
    Return a CaptionVariant only if it belongs (via its request) to the current user.
    """
    variant = session.exec(
        select(CaptionVariant)
        .join(CaptionRequest, CaptionVariant.request_id == CaptionRequest.id)
        .where(
            CaptionVariant.id == variant_id,
            CaptionRequest.user_id == current_user.id,
        )
    ).one_or_none()

    if not variant:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CaptionVariant not found")

    return variant


def delete_caption_variant(
    variant_id: str,
    session: Session,
    current_user: User,
) -> None:
    """
    Delete a CaptionVariant only if it belongs to the current user.
    """
    variant = session.exec(
        select(CaptionVariant)
        .join(CaptionRequest, CaptionVariant.request_id == CaptionRequest.id)
        .where(
            CaptionVariant.id == variant_id,
            CaptionRequest.user_id == current_user.id,
        )
    ).one_or_none()

    if not variant:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CaptionVariant not found")

    session.delete(variant)
    session.commit()
    logger.info("CaptionVariant %s deleted", variant_id)


def list_caption_variants(
    session: Session,
    current_user: User,
) -> CaptionVariantList:
    """
    List all of a user's CaptionVariants via their CaptionRequests.
    """
    rows = session.exec(
        select(CaptionVariant)
        .join(CaptionRequest, CaptionVariant.request_id == CaptionRequest.id)
        .where(CaptionRequest.user_id == current_user.id)
    ).all()

    logger.info("Listing %d variants for User %s", len(rows), current_user.id)
    return CaptionVariantList(variants=rows)
