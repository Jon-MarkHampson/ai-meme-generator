import logging
from fastapi import HTTPException, status
from sqlmodel import Session, select

from entities.caption_requests import CaptionRequest
from entities.meme_templates import MemeTemplate
from entities.caption_variants import CaptionVariant
from entities.user import User
from .models import (
    CaptionRequestCreate,
    CaptionRequestRead,
    CaptionRequestUpdate,
    CaptionRequestList,
)

logger = logging.getLogger(__name__)


def create_caption_request(
    data: CaptionRequestCreate,
    session: Session,
    current_user: User,
) -> CaptionRequestRead:
    """
    Create and persist a new CaptionRequest for the current user.
    """
    cr = CaptionRequest(**data.model_dump(), user_id=current_user.id)
    session.add(cr)
    session.commit()
    session.refresh(cr)
    logger.info("CaptionRequest %s created by User %s", cr.id, current_user.id)
    return cr


def read_caption_request(
    request_id: str,
    session: Session,
    current_user: User,
) -> CaptionRequestRead:
    """
    Return the given CaptionRequest, if it exists and belongs to current_user.
    """
    cr = session.get(CaptionRequest, request_id)
    if not cr:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Caption request not found")
    if cr.user_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not permitted")
    return cr


def update_caption_request(
    request_id: str,
    data: CaptionRequestUpdate,
    session: Session,
    current_user: User,
) -> CaptionRequestRead:
    """
    Patch fields on an existing CaptionRequest.
    Validates that any new meme_template_id or chosen_variant_id actually exists.
    """
    cr = session.get(CaptionRequest, request_id) or HTTPException(
        status.HTTP_404_NOT_FOUND, "Caption request not found"
    )
    if cr.user_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not permitted")

    updates = data.model_dump(exclude_unset=True)

    # If they're changing the base template, make sure it exists
    if "meme_template_id" in updates:
        mt = updates["meme_template_id"]
        if (
            mt is not None
            and not session.exec(
                select(MemeTemplate.id).where(MemeTemplate.id == mt)
            ).first()
        ):
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                f"MemeTemplate {mt!r} not found",
            )
        cr.meme_template_id = mt

    # If they're picking a variant, make sure it exists
    if "chosen_variant_id" in updates:
        cv = updates["chosen_variant_id"]
        if (
            cv is not None
            and not session.exec(
                select(CaptionVariant.id).where(CaptionVariant.id == cv)
            ).first()
        ):
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                f"CaptionVariant {cv!r} not found",
            )
        cr.chosen_variant_id = cv

    session.commit()
    session.refresh(cr)
    logger.info("CaptionRequest %s updated by User %s", cr.id, current_user.id)
    return cr


def delete_caption_request(
    request_id: str,
    session: Session,
    current_user: User,
) -> None:
    """
    Delete an existing CaptionRequest if it belongs to current_user.
    """
    cr = session.get(CaptionRequest, request_id)
    if not cr:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Caption request not found")
    if cr.user_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not permitted")
    session.delete(cr)
    session.commit()
    logger.info("CaptionRequest %s deleted by User %s", request_id, current_user.id)


def list_caption_requests(
    session: Session,
    current_user: User,
) -> CaptionRequestList:
    """
    Return a list of all CaptionRequests for the current user.
    """
    rows = session.exec(
        select(CaptionRequest).where(CaptionRequest.user_id == current_user.id)
    ).all()
    logger.info("Listing %d caption requests for User %s", len(rows), current_user.id)
    return CaptionRequestList(requests=rows)
