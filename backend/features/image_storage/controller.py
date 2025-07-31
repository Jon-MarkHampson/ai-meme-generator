"""
Image storage controller handling file upload and retrieval operations.

This module provides HTTP endpoints for managing image assets in the meme
generation system, interfacing with Supabase storage for secure file handling.
It supports image uploads with validation and public URL retrieval for
displaying stored images.

Key features:
- Secure image upload with file type validation
- Supabase storage integration for reliable file hosting
- Public URL generation for frontend image display
- User authentication enforcement for all operations
- Comprehensive error handling and logging

Supported formats:
- PNG: Lossless format ideal for memes with text overlays
- JPEG: Compressed format for photographic content
- GIF: Animated format support for dynamic memes

Security considerations:
- All endpoints require authenticated users
- File type validation prevents malicious uploads
- Secure storage bucket configuration
- Proper error handling prevents information leakage

Technical integration:
Works closely with the meme generation service to store AI-generated
images and provide persistent URLs for user galleries and sharing.
"""
import logging
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from features.auth.service import get_current_user
from entities.user import User
from .service import (
    upload_image_to_supabase,
    get_image_url_from_supabase,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/image", tags=["image"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Upload an image for the authenticated user",
)
async def upload_image(
    storage_bucket: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Upload an image file to Supabase storage with validation and security checks.
    
    This endpoint handles multipart file uploads, validates file types for security,
    and stores images in Supabase storage buckets. Used by the meme generation
    system to persist AI-generated images and by users for custom uploads.
    
    Args:
        storage_bucket: Target storage bucket name for file organization
        file: Uploaded file from multipart/form-data request
        current_user: Authenticated user from JWT token validation
        
    Returns:
        Dict containing the public URL of the uploaded image
        
    Raises:
        HTTPException: 400 if file type is invalid (not PNG/JPEG/GIF)
        HTTPException: 500 if Supabase storage operation fails
        
    Security measures:
        - File type validation prevents malicious uploads
        - Content type checking ensures only image files are accepted
        - User authentication required for all uploads
        - Comprehensive error logging for security monitoring
        
    Usage context:
        - AI-generated meme storage after creation
        - User custom image uploads for meme templates
        - Profile picture or asset uploads
        
    Technical details:
        - Reads entire file into memory for upload
        - Generates unique filenames to prevent conflicts
        - Returns public URLs for immediate frontend use
    """
    logger.info(
        f"User {current_user.id} is uploading file "
        f"'{file.filename}' (type={file.content_type})"
    )

    # Validate file type to prevent malicious uploads
    if file.content_type not in {"image/png", "image/jpeg", "image/gif"}:
        logger.error("Invalid image type. Only PNG/JPEG/GIF allowed.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image type. Only PNG/JPEG/GIF allowed.",
        )

    # Read file contents for Supabase upload
    contents = await file.read()
    logger.debug(f"Read {len(contents)} bytes from '{file.filename}'")

    # Upload to Supabase storage with error handling
    try:
        public_url = upload_image_to_supabase(storage_bucket, contents, file.filename)
    except Exception:
        logger.warning("Failed to upload image to Supabase")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload image. Please try again later.",
        )

    logger.info(
        f"Image '{file.filename}' uploaded successfully for user "
        f"{current_user.id}. URL: {public_url}"
    )
    return {"url": public_url}


@router.get(
    "/",
    response_model=str,
    summary="Get the public URL of an uploaded image",
)
async def get_image_url(
    image_id: str,
    storage_bucket: str,
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve the public URL of a stored image by its identifier.
    
    This endpoint provides access to previously uploaded images by generating
    or retrieving their public URLs from Supabase storage. Used when displaying
    images in galleries, chat interfaces, or sharing contexts.
    
    Args:
        image_id: Unique identifier of the image to retrieve
        storage_bucket: Storage bucket containing the target image
        current_user: Authenticated user from JWT token validation
        
    Returns:
        str: Public URL of the requested image
        
    Raises:
        HTTPException: 404 if image not found in specified bucket
        HTTPException: 403 if user lacks access to the image
        HTTPException: 500 if storage service is unavailable
        
    Security considerations:
        - User authentication required for all requests
        - Access control enforced at the service layer
        - Image ownership validation where applicable
        
    Usage context:
        - Loading images for gallery display
        - Retrieving meme images for chat interfaces
        - Generating shareable links for user content
        
    Technical note:
        The URL generation may involve Supabase signed URLs for private
        content or direct public URLs for publicly accessible images.
    """
    logger.info(f"User {current_user.id} requested URL for image ID {image_id}")
    return get_image_url_from_supabase(image_id, storage_bucket, current_user)
