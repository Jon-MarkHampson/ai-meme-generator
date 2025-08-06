"""
User meme controller providing CRUD endpoints for generated meme management.

This module exposes HTTP endpoints for users to manage their AI-generated memes,
including viewing collections, marking favorites, and organizing their creative
work. All endpoints enforce user ownership to ensure data privacy and security.

Key features:
- Complete CRUD operations for user memes
- Favorite meme management for user collections
- Ownership-based access control on all operations
- RESTful API design with proper HTTP status codes
- Gallery support for browsing user's meme history

Security considerations:
- All endpoints require authentication via JWT tokens
- User ownership validation prevents accessing other users' memes
- Proper HTTP status codes provide clear API responses
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from database.core import get_session
from features.users.model import User
from features.auth.service import get_current_user
from .schema import UserMemeCreate, UserMemeRead, UserMemeUpdate, UserMemeList
from .service import (
    create_user_meme as service_create,
    read_user_meme as service_read,
    update_user_meme as service_update,
    delete_user_meme as service_delete,
    list_user_memes as service_list,
    get_favorite_memes as service_get_favorite_memes,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/user_memes", tags=["user_memes"])


@router.post(
    "/",
    response_model=UserMemeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user meme.",
)
def create_user_meme(
    data: UserMemeCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UserMemeRead:
    """
    Create a new meme record for the authenticated user.
    
    This endpoint is typically called by the AI generation system to persist
    meme metadata after successful image creation. It associates the meme
    with the user and conversation context for future reference.
    
    Args:
        data: Meme creation payload with image URL and conversation details
        session: Database session from dependency injection
        current_user: Authenticated user from JWT token validation
        
    Returns:
        UserMemeRead: Created meme with generated ID and timestamps
        
    Raises:
        HTTPException: 400 if required fields are missing
    """
    return service_create(data, session, current_user)


@router.get(
    "/",
    response_model=UserMemeList,
    summary="List all user memes.",
)
def list_user_memes(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UserMemeList:
    """
    Retrieve all memes created by the authenticated user.
    
    Used by the gallery interface to display the user's complete meme
    collection. Results are ordered by creation date (newest first)
    to showcase recent creative work prominently.
    
    Args:
        session: Database session from dependency injection
        current_user: Authenticated user from JWT token validation
        
    Returns:
        UserMemeList: Container with all user's memes ordered by recency
        
    Note:
        Currently returns all memes without pagination. Consider adding
        pagination for users with large collections in the future.
    """
    return service_list(session, current_user)


@router.get(
    "/favorites",
    response_model=UserMemeList,
    summary="List all favorite user memes.",
)
def get_favorite_memes(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UserMemeList:
    """
    Retrieve only the user's favorite memes for curated collections.
    
    Provides a filtered view of memes the user has marked as favorites,
    perfect for showcasing their best work or quickly accessing preferred
    memes. Used by dedicated favorites gallery views.
    
    Args:
        session: Database session from dependency injection
        current_user: Authenticated user from JWT token validation
        
    Returns:
        UserMemeList: Container with user's favorite memes only
        
    Business context:
        Users can mark memes as favorites during or after generation
        to build curated collections of their best creative work.
    """
    return service_get_favorite_memes(session, current_user)


@router.get(
    "/{meme_id}",
    response_model=UserMemeRead,
    summary="Get a user meme by ID.",
)
def get_user_meme(
    meme_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UserMemeRead:
    """
    Retrieve a specific meme by its unique identifier.
    
    Used for displaying individual memes in detail views or when the
    frontend needs to fetch specific meme data. Enforces ownership
    validation to ensure users can only access their own memes.
    
    Args:
        meme_id: Unique identifier of the meme to retrieve
        session: Database session from dependency injection
        current_user: Authenticated user from JWT token validation
        
    Returns:
        UserMemeRead: Complete meme data including metadata
        
    Raises:
        HTTPException: 404 if meme not found or not owned by user
        
    Security note:
        Ownership validation prevents users from accessing other users'
        private meme collections through ID enumeration attacks.
    """
    return service_read(session, current_user, meme_id)


@router.patch(
    "/{meme_id}",
    response_model=UserMemeRead,
    summary="Update a user meme by ID.",
)
def update_user_meme(
    meme_id: str,
    data: UserMemeUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UserMemeRead:
    """
    Update meme properties such as favorite status.
    
    Currently supports updating the favorite flag to allow users to
    curate their meme collections. Uses partial updates (PATCH) to
    modify only specified fields while preserving existing data.
    
    Args:
        meme_id: Unique identifier of the meme to update
        data: Update payload with fields to modify (currently favorite status)
        session: Database session from dependency injection
        current_user: Authenticated user from JWT token validation
        
    Returns:
        UserMemeRead: Updated meme data with new field values
        
    Raises:
        HTTPException: 404 if meme not found or not owned by user
        
    Future enhancements:
        Could support updating meme titles, descriptions, or tags
        for better organization and searchability.
    """
    return service_update(meme_id, data, session, current_user)


@router.delete(
    "/{meme_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user meme by ID.",
)
def delete_user_meme(
    meme_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Permanently delete a user's meme from their collection.
    
    Removes the meme metadata from the database. Note that this only
    deletes the database record - the actual image file remains in
    Supabase storage and would need separate cleanup.
    
    Args:
        meme_id: Unique identifier of the meme to delete
        session: Database session from dependency injection
        current_user: Authenticated user from JWT token validation
        
    Returns:
        None: 204 No Content status indicates successful deletion
        
    Raises:
        HTTPException: 404 if meme not found or not owned by user
        
    Important:
        Deletion is permanent and cannot be undone. Users should be
        warned before confirming deletion of their creative work.
        
    TODO:
        Implement cleanup of associated image files in Supabase storage
        to prevent orphaned files and manage storage costs.
    """
    service_delete(meme_id, session, current_user)
