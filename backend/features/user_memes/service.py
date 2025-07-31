"""
User meme management service handling CRUD operations for generated memes.

This service manages the lifecycle of user-generated memes, from creation
during AI generation to user management of favorites and collections.
All operations enforce user ownership for security and data isolation.

Key features:
- Secure meme creation with validation
- Ownership-based access control
- Favorite meme management
- Conversation context tracking
- Comprehensive error handling with logging
"""

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
    """
    Create a new meme record for the user.
    
    Called automatically during AI generation to persist meme metadata
    and provide tracking for user collections. Validates required fields
    and enforces user ownership.
    
    Args:
        data: Meme creation payload with image URL and conversation context
        session: Database session for transaction management
        current_user: Authenticated user who owns the meme
        
    Returns:
        UserMemeRead: Created meme with generated ID and timestamps
        
    Raises:
        HTTPException: 400 if required fields are missing
    """
    # Initialize meme with user ownership
    user_meme = UserMeme(**data.model_dump(), user_id=current_user.id)

    # Validate essential meme data
    if not user_meme.image_url:
        logger.warning(
            f"User {current_user.id} attempted to create UserMeme without image URL"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image URL is required",
        )
    
    # TODO: Add meme template validation when template system is implemented
    # Current system uses direct AI generation without predefined templates

    # Persist meme record
    session.add(user_meme)
    session.commit()
    session.refresh(user_meme)  # Get generated timestamps and ID

    logger.info(f"Created meme {user_meme.id} for user {current_user.id}")
    return UserMemeRead.model_validate(user_meme)


def read_user_meme(
    session: Session,
    current_user: User,
    meme_id: str,
) -> UserMemeRead:
    """
    Retrieve a specific meme belonging to the authenticated user.

    Enforces user ownership to prevent accessing other users' memes.
    Used for displaying individual memes and modification workflows.

    Args:
        session: Database session for query execution
        current_user: User requesting the meme
        meme_id: Unique identifier of the meme to retrieve

    Returns:
        UserMemeRead: Meme data if found and owned by user

    Raises:
        HTTPException: 404 if meme not found or not owned by user
    """
    # Query with ownership filter for security
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

    return UserMemeRead.model_validate(user_meme)


def read_latest_conversation_meme(
    conversation_id: str,
    session: Session,
    current_user: User,
) -> UserMemeRead:
    """
    Get the most recent meme from a specific conversation.

    Used by AI agents to reference the previous meme for modification
    requests or context. Essential for the iterative meme refinement
    workflow.

    Args:
        conversation_id: UUID of the conversation to search
        session: Database session for query execution
        current_user: User who owns the conversation

    Returns:
        UserMemeRead: Most recent meme from conversation, or None if none found

    Note:
        Returns None rather than raising exception to allow graceful handling
        when no memes exist in a conversation yet.
    """
    # Get newest meme from conversation with user ownership check
    statement = (
        select(UserMeme)
        .where(
            UserMeme.conversation_id == conversation_id,
            UserMeme.user_id == current_user.id,
        )
        .order_by(UserMeme.created_at.desc())
    )
    user_meme = session.exec(statement).first()

    if not user_meme:
        logger.info(
            f"No memes found in conversation {conversation_id} for user {current_user.id}"
        )
        return None

    logger.info(f"Retrieved latest meme {user_meme.id} for user {current_user.id}")
    return UserMemeRead.model_validate(user_meme)


def update_user_meme(
    meme_id: str,
    data: UserMemeUpdate,
    session: Session,
    current_user: User,
) -> UserMemeRead:
    """
    Update meme properties like favorite status.

    Currently supports updating the favorite flag for user collections.
    Uses partial updates to modify only specified fields while preserving
    existing data.

    Args:
        meme_id: ID of the meme to update
        data: Update payload with fields to modify
        session: Database session for transaction management
        current_user: User requesting the update

    Returns:
        UserMemeRead: Updated meme data

    Raises:
        HTTPException: 404 if meme not found or not owned by user
    """
    # Locate meme with ownership verification
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

    # Apply partial updates to specified fields only
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(user_meme, key, value)

    session.add(user_meme)
    session.commit()
    session.refresh(user_meme)

    logger.info(f"Updated meme {meme_id} for user {current_user.id}")
    return UserMemeRead.model_validate(user_meme)


def delete_user_meme(
    meme_id: str,
    session: Session,
    current_user: User,
) -> None:
    """
    Permanently delete a user's meme.

    Removes the meme record from the database. Note that this only
    deletes the metadata - the actual image file remains in storage
    and would need separate cleanup.

    Args:
        meme_id: ID of the meme to delete
        session: Database session for transaction management
        current_user: User requesting the deletion

    Raises:
        HTTPException: 404 if meme not found or not owned by user

    TODO: Implement image cleanup from Supabase storage
    """
    # Find meme with ownership check
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
    """
    Retrieve all memes created by the authenticated user.

    Returns the complete collection of user's memes for gallery display
    or management interfaces. Results are not paginated currently.

    Args:
        session: Database session for query execution
        current_user: User whose memes to retrieve

    Returns:
        UserMemeList: Container with list of user's memes

    TODO: Add pagination for users with large meme collections
    """
    # Get all user's memes ordered by creation date
    statement = (
        select(UserMeme)
        .where(UserMeme.user_id == current_user.id)
        .order_by(UserMeme.created_at.desc())
    )
    memes = session.exec(statement).all()

    if not memes:
        logger.info(f"User {current_user.id} has no memes")
        return UserMemeList(memes=[])

    logger.info(f"Listed {len(memes)} memes for user {current_user.id}")
    # Transform database models to API response format
    meme_models = [UserMemeRead.model_validate(meme) for meme in memes]
    return UserMemeList(memes=meme_models)


def get_favorite_memes(
    session: Session,
    current_user: User,
) -> UserMemeList:
    """
    Retrieve user's favorite memes for curated collections.

    Filters to only memes marked as favorites, ordered by creation date.
    Used for dedicated favorites views and highlighting special memes.

    Args:
        session: Database session for query execution
        current_user: User whose favorites to retrieve

    Returns:
        UserMemeList: Container with user's favorite memes
    """
    # Query favorite memes ordered by recency
    statement = (
        select(UserMeme)
        .where(UserMeme.user_id == current_user.id, UserMeme.is_favorite == True)
        .order_by(UserMeme.created_at.desc())
    )
    favorite_memes = session.exec(statement).all()

    if not favorite_memes:
        logger.info(f"User {current_user.id} has no favorite memes")
        return UserMemeList(memes=[])

    logger.info(
        f"Retrieved {len(favorite_memes)} favorite memes for user {current_user.id}"
    )
    # Convert to API response format
    meme_models = [UserMemeRead.model_validate(meme) for meme in favorite_memes]
    return UserMemeList(memes=meme_models)
