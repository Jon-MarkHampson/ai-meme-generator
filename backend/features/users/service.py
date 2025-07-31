"""
User profile management service handling account operations.

This service provides secure user account management including profile
updates and account deletion. All operations require password verification
to prevent unauthorized changes, following security best practices.

Key security features:
- Current password verification for all profile changes
- Secure password hashing with bcrypt
- Comprehensive audit logging
- Atomic database transactions
"""
import logging
from fastapi import HTTPException, status
from sqlmodel import Session

from entities.user import User
from .models import UserUpdate, UserDelete
from utils.security import get_password_hash, verify_password


logger = logging.getLogger(__name__)


def read_current_user(current_user: User) -> User:
    """
    Return the current authenticated user's data.
    
    Args:
        current_user: The authenticated User object from dependency injection
        
    Returns:
        User object (controller handles conversion to UserRead)
    """
    return current_user


def update_current_user(
    user_update: UserUpdate,
    session: Session,
    current_user: User,
) -> User:
    """
    Update user profile with validation and password verification.
    
    Args:
        user_update: UserUpdate model with fields to change
        session: Database session for executing queries
        current_user: The authenticated User object
        
    Returns:
        Updated User object
        
    Raises:
        HTTPException: If current password verification fails
    """
    data = user_update.model_dump(exclude_unset=True)

    # Verify current password before allowing any changes
    supplied_old_pw = data.pop("current_password", None)

    if not verify_password(supplied_old_pw, current_user.hashed_password):
        logger.warning(
            f"User {current_user.id} attempted to update profile with incorrect password."
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect.",
        )
    logger.info(f"User {current_user.id} verified their current password successfully.")

    # Handle password change if requested
    if "password" in data:
        new_pw = data.pop("password")
        current_user.hashed_password = get_password_hash(new_pw)
        logger.info(f"User {current_user.id} updated their password successfully.")

    # Update profile fields that were provided
    if "first_name" in data:
        current_user.first_name = data["first_name"]
        logger.info(f"User {current_user.id} updated their first name successfully.")
    if "last_name" in data:
        current_user.last_name = data["last_name"]
        logger.info(f"User {current_user.id} updated their last name successfully.")
    if "email" in data:
        current_user.email = data["email"]
        logger.info(f"User {current_user.id} updated their email successfully.")
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user


def delete_current_user(
    delete_in: UserDelete,
    session: Session,
    current_user: User,
) -> None:
    """
    Permanently delete user account with password confirmation.
    
    Requires password verification for security. Deletion cascades to
    remove all associated data (conversations, memes, messages) due to
    foreign key constraints with CASCADE delete configured.
    
    Args:
        delete_in: Deletion request containing password confirmation
        session: Database session for transaction management
        current_user: Authenticated user requesting deletion
        
    Raises:
        HTTPException: 401 if password verification fails
        
    Note:
        This operation is irreversible. All user data is permanently removed.
    """
    # Verify password before allowing destructive operation
    if not verify_password(delete_in.password, current_user.hashed_password):
        logger.warning(
            f"User {current_user.id} attempted to delete account with incorrect password."
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password, cannot delete account.",
        )
    
    logger.info(f"User {current_user.id} is deleting their account.")
    
    # Cascade deletion removes all associated data
    session.delete(current_user)
    session.commit()
    
    # Return None; controller returns 204 No Content automatically
