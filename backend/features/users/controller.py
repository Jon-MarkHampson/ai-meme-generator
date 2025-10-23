"""
User profile controller providing self-service endpoints for account management.

This module exposes HTTP endpoints for authenticated users to manage their own
profiles, following the principle of user ownership where individuals can only
access and modify their own account data. All operations require active
authentication to ensure security.

Key features:
- Profile viewing for user dashboard display
- Account updates including name and email changes  
- Secure account deletion with password confirmation
- RESTful API design with appropriate HTTP methods
- Complete audit logging for security monitoring

Security considerations:
- All endpoints require valid JWT authentication
- Users can only access their own profile data
- Account deletion requires password re-verification
- Sensitive operations are fully logged for audit trails
- No administrative access to other users' accounts

Architecture note:
This controller follows the established pattern of thin controllers that
delegate business logic to service layers, maintaining clean separation
of concerns and testability.
"""
import logging

from fastapi import APIRouter, Body, Depends, status
from sqlmodel import Session

from database.core import get_session
from features.auth.service import get_current_user
from features.users.model import User

from .schema import UserDelete, UserRead, UserUpdate
from .service import (delete_current_user, read_current_user,
                      update_current_user)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserRead,
    summary="Return the currently authenticated user.",
)
def read_me(
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve the authenticated user's profile information.
    
    This endpoint provides access to the current user's profile data for
    displaying in dashboard interfaces, profile pages, or user settings.
    The response excludes sensitive fields like password hashes.
    
    Args:
        current_user: Authenticated user from JWT token validation
        
    Returns:
        UserRead: Sanitized user profile with public information only
        
    Usage context:
        Frontend calls this on app initialization to populate user
        interface elements and verify authentication status.
        
    Security note:
        Only returns the authenticated user's own data - no user ID
        parameter needed as identity comes from the JWT token.
    """
    logger.info(f"GET /users/me - user_id={current_user.id}")
    return read_current_user(current_user)


@router.patch(
    "/me",
    response_model=UserRead,
    summary="Update current user's profile fields and return the updated user.",
)
def update_me(
    user_update: UserUpdate = Body(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Update the authenticated user's profile information.
    
    Allows users to modify their account details such as display name,
    email address, or other profile fields. Uses PATCH semantics to
    support partial updates - only provided fields are modified.
    
    Args:
        user_update: Update payload containing fields to modify
        session: Database session for persistence operations
        current_user: Authenticated user from JWT token validation
        
    Returns:
        UserRead: Updated user profile with new field values
        
    Raises:
        HTTPException: 400 if validation fails (e.g., email already exists)
        HTTPException: 422 if update data format is invalid
        
    Business logic:
        - Email uniqueness is enforced at the database level
        - Profile changes take effect immediately
        - Updated data is returned for frontend state sync
        
    Security considerations:
        - Users can only update their own profiles
        - Sensitive fields like password require separate endpoints
        - All changes are logged for audit purposes
    """
    logger.info(
        f"PATCH /users/me - user_id={current_user.id}, update={user_update.model_dump()}"
    )
    return update_current_user(
        user_update=user_update,
        session=session,
        current_user=current_user,
    )


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete current user account (requires password).",
)
def delete_me(
    delete_in: UserDelete,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Permanently delete the authenticated user's account.
    
    This is a destructive operation that removes the user's account and
    associated data from the system. Password confirmation is required
    as an additional security measure to prevent accidental deletions.
    
    Args:
        delete_in: Deletion payload containing password confirmation
        session: Database session for transaction management
        current_user: Authenticated user from JWT token validation
        
    Returns:
        None: 204 No Content status indicates successful deletion
        
    Raises:
        HTTPException: 400 if password confirmation fails
        HTTPException: 422 if deletion payload is invalid
        
    Security measures:
        - Password re-verification prevents unauthorized account deletion
        - Only the account owner can delete their own account
        - Operation is logged for security audit trails
        
    Data implications:
        - User account and profile data are permanently removed
        - Associated memes and conversations may be preserved or deleted
        - Action cannot be undone once completed
        
    Important:
        Frontend should display clear warnings and confirmation dialogs
        before calling this endpoint to prevent accidental data loss.
    """
    logger.info(f"DELETE /users/me - user_id={current_user.id}")
    delete_current_user(
        delete_in=delete_in,
        session=session,
        current_user=current_user,
    )
    return  # 204 No Content indicates successful deletion
