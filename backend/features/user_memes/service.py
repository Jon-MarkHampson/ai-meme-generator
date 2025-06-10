import logging
from fastapi import HTTPException, status
from sqlmodel import Session, select
from entities.user_memes import UserMeme
from entities.user import User
from .models import (
    UserMemeCreate,
    UserMemeRead,
    UserMemeList,
    UserMemeUpdate,
)

logger = logging.getLogger(__name__)


def create_user_meme(
    data: UserMemeCreate,
    session: Session,
    current_user: User,
) -> UserMemeRead:
    # Create the UserMeme object
    user_meme = UserMeme(**data.model_dump(), user_id=current_user.id)

    # Validate all required fields
    if not user_meme.image_url:
        logger.warning(
            f"User {current_user.id} attempted to create UserMeme without image URL"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image URL is required",
        )
    # UNCOMMENT THIS ONCE THE MEME TEMPLATE ID IS REQUIRED

    # if not user_meme.meme_template_id:
    #     logger.warning(
    #         f"User {current_user.id} attempted to create UserMeme without meme template ID"
    #     )
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Meme template ID is required",
    #     )
    # Check if the meme template exists
    # statement = select(UserMeme).where(
    #     UserMeme.meme_template_id == user_meme.meme_template_id
    # )

    # if not session.exec(statement).first():
    #     logger.warning(
    #         f"User {current_user.id} attempted to create UserMeme with non-existent MemeTemplate {user_meme.meme_template_id}"
    #     )
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail=f"MemeTemplate {user_meme.meme_template_id!r} not found",
    #     )

    session.add(user_meme)
    session.commit()
    session.refresh(user_meme)

    return user_meme


def read_user_meme(
    session: Session,
    current_user: User,
    meme_id: str,
) -> UserMemeRead:
    statement = select(UserMeme).where(
        UserMeme.id == meme_id, UserMeme.user_id == current_user.id
    )
    user_meme = session.exec(statement).first()

    if not user_meme:
        logger.warning(
            f"User {current_user.id} attempted to access non-existent UserMeme {meme_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"UserMeme {meme_id!r} not found",
        )

    return user_meme


def update_user_meme(
    meme_id: str,
    data: UserMemeUpdate,
    session: Session,
    current_user: User,
) -> UserMemeRead:
    statement = select(UserMeme).where(
        UserMeme.id == meme_id, UserMeme.user_id == current_user.id
    )
    user_meme = session.exec(statement).first()

    if not user_meme:
        logger.warning(
            f"User {current_user.id} attempted to update non-existent UserMeme {meme_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"UserMeme {meme_id!r} not found",
        )

    # Update the fields
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(user_meme, key, value)

    session.add(user_meme)
    session.commit()
    session.refresh(user_meme)

    return user_meme


def delete_user_meme(
    meme_id: str,
    session: Session,
    current_user: User,
) -> None:
    statement = select(UserMeme).where(
        UserMeme.id == meme_id, UserMeme.user_id == current_user.id
    )
    user_meme = session.exec(statement).first()

    if not user_meme:
        logger.warning(
            f"User {current_user.id} attempted to delete non-existent UserMeme {meme_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"UserMeme {meme_id!r} not found",
        )

    session.delete(user_meme)
    session.commit()
    logger.info(f"UserMeme {meme_id} deleted by User {current_user.id}")


def list_user_memes(
    session: Session,
    current_user: User,
) -> UserMemeList:
    statement = select(UserMeme).where(UserMeme.user_id == current_user.id)
    memes = session.exec(statement).all()

    if not memes:
        logger.info(f"User {current_user.id} has no memes")
        return UserMemeList(memes=[])

    logger.info(f"Listed {len(memes)} memes for user {current_user.id}")
    return UserMemeList(memes=memes)
