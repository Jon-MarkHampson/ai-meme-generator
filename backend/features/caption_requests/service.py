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

    cr = CaptionRequest(**data.model_dump(), user_id=current_user.id)
    if not cr.prompt_text:
        logger.exception(
            f"User {current_user.id} attempted to create CaptionRequest without prompt text"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Prompt text is required"
        )
    if not cr.request_method:
        logger.exception(
            f"User {current_user.id} attempted to create CaptionRequest without request method"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Request method is required"
        )

    session.add(cr)
    session.commit()
    session.refresh(cr)

    logger.info(f"CaptionRequest {cr.id} created by User {current_user.id}")
    return cr


def read_caption_request(
    request_id: str,
    session: Session,
    current_user: User,
) -> CaptionRequestRead:
    cr = session.get(CaptionRequest, request_id)
    if not cr:
        logger.exception(f"CaptionRequest {request_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if cr.user_id != current_user.id:
        logger.exception(
            f"User {current_user.id} not authorized to read CaptionRequest {request_id}"
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    logger.info(f"CaptionRequest {cr.id} read by User {current_user.id}")
    return cr


def update_caption_request(
    request_id: str,
    data: CaptionRequestUpdate,
    session: Session,
    current_user: User,
) -> CaptionRequestRead:
    cr = session.get(CaptionRequest, request_id)
    if not cr:
        logger.exception(f"CaptionRequest {request_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="CaptionRequest not found"
        )
    if cr.user_id != current_user.id:
        logger.exception(
            f"User {current_user.id} not authorized to update CaptionRequest {request_id}"
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    updates = data.model_dump(exclude_unset=True)

    # validate meme_template_id FK
    if "meme_template_id" in updates:
        meme_template_id = updates["meme_template_id"]
        if meme_template_id is not None:
            template_exists = session.exec(
                select(MemeTemplate.id).where(MemeTemplate.id == meme_template_id)
            ).first()
            if not template_exists:
                logger.exception(
                    f"MemeTemplate {meme_template_id} not found for CaptionRequest {request_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"MemeTemplate {meme_template_id!r} not found",
                )
        cr.meme_template_id = meme_template_id

    # validate chosen_variant_id FK
    if "chosen_variant_id" in updates:
        chosen_variant_id = updates["chosen_variant_id"]
        if chosen_variant_id is not None:
            variant_exists = session.exec(
                select(CaptionVariant.id).where(CaptionVariant.id == chosen_variant_id)
            ).first()
            if not variant_exists:
                logger.exception(
                    f"CaptionVariant {chosen_variant_id} not found for CaptionRequest {request_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"CaptionVariant {chosen_variant_id!r} not found",
                )
        cr.chosen_variant_id = chosen_variant_id

    session.commit()
    session.refresh(cr)

    logger.info(f"CaptionRequest {cr.id} updated by User {current_user.id}")
    return cr


def delete_caption_request(
    request_id: str,
    session: Session,
    current_user: User,
) -> None:
    cr = session.get(CaptionRequest, request_id)
    if not cr:
        logger.exception(f"CaptionRequest {request_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if cr.user_id != current_user.id:
        logger.exception(
            f"User {current_user.id} not authorized to delete CaptionRequest {request_id}"
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    session.delete(cr)
    session.commit()

    logger.info(f"CaptionRequest {request_id} deleted by User {current_user.id}")
    return None


def list_caption_requests(
    session: Session,
    current_user: User,
) -> CaptionRequestList:
    rows = session.exec(
        select(CaptionRequest).where(CaptionRequest.user_id == current_user.id)
    ).all()
    logger.info(f"Listing {len(rows)} caption requests for User {current_user.id}")
    return CaptionRequestList(requests=rows)
