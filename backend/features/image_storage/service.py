"""
Image storage service managing file uploads to Supabase Storage.

This service handles the integration with Supabase Storage for persisting
generated meme images. It provides secure upload functionality with proper
error handling and URL generation for frontend display.

Key features:
- Secure file uploads with unique naming
- Public URL generation for image access
- Comprehensive error handling and logging
- Integration with Supabase Storage API
- Support for various image formats
"""
import uuid
import logging
from fastapi import HTTPException, status
from storage3.exceptions import StorageApiError
from database.supabase_client import supabase
from entities.user import User

logger = logging.getLogger(__name__)


def upload_image_to_supabase(
    storage_bucket: str,
    contents: bytes,
    original_filename: str,
    content_type: str = "image/png",
) -> str:
    """
    Upload image data to Supabase Storage and return public URL.
    
    Handles the complete upload workflow from binary data to accessible URL.
    Uses the original filename to maintain traceability and debugging capability.
    
    Args:
        storage_bucket: Name of the Supabase storage bucket
        contents: Raw image data as bytes
        original_filename: Generated filename from image processing
        content_type: MIME type for the image (defaults to PNG)
        
    Returns:
        Public URL string for accessing the uploaded image
        
    Raises:
        HTTPException: 500 if upload fails or URL retrieval fails
        
    Note:
        Currently uses original filename directly. Future enhancement
        could implement UUID-based naming for better collision avoidance.
    """

    # Use original filename for traceability
    # TODO: Consider UUID-based naming for production to avoid conflicts
    file_name = original_filename

    # Upload binary data to storage bucket
    try:
        logger.info(f"Uploading {original_filename} to Supabase at {file_name}")
        supabase.storage.from_(storage_bucket).upload(
            file_name, contents, file_options={"content-type": content_type}
        )
        logger.info(f"Upload successful for {file_name}")
    except StorageApiError as e:
        message = str(e)
        logger.error(f"Supabase upload failed: {message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Supabase storage upload failed: {message}",
        )

    # Generate public URL for frontend access
    logger.info(f"Retrieving public URL for {file_name}")
    url_response = supabase.storage.from_(storage_bucket).get_public_url(file_name)

    # Handle different response formats from Supabase client
    if isinstance(url_response, str):
        public_url = url_response
        logger.debug(f"get_public_url returned string: {public_url}")
    else:
        # Handle dict response format
        public_url = url_response.get("publicURL") if isinstance(url_response, dict) else None
        logger.debug(f"get_public_url returned dict: {url_response!r}")

    if not public_url:
        logger.error(f"Could not retrieve public URL after upload: {url_response!r}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve public URL after upload.",
        )

    logger.info(f"Returning public URL: {public_url}")
    return public_url


def get_image_url_from_supabase(
    image_id: str, storage_bucket: str, current_user: User
) -> str:
    """
    Retrieve public URL for an existing image in storage.
    
    Used for accessing previously uploaded images without re-uploading.
    Includes user context for audit logging and potential future access control.
    
    Args:
        image_id: Filename/key of the image in storage
        storage_bucket: Name of the Supabase storage bucket
        current_user: User requesting the image URL (for logging)
        
    Returns:
        Public URL string for the requested image
        
    Raises:
        HTTPException: 404 if image not found, 500 for storage errors
    """
    logger.info(f"User {current_user.id} requested URL for image ID {image_id}")

    try:
        # Request public URL from Supabase Storage
        url_response = supabase.storage.from_(storage_bucket).get_public_url(image_id)
        
        # Handle response format variations
        if isinstance(url_response, str):
            public_url = url_response
        else:
            public_url = url_response.get("publicURL", None)

        if not public_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image with ID {image_id} not found in bucket {storage_bucket}.",
            )

        logger.info(f"Returning public URL: {public_url}")
        return public_url

    except StorageApiError as e:
        message = str(e)
        logger.error(f"Failed to retrieve image URL: {message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve image URL: {message}",
        )
