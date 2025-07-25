# backend/features/image_storage/controller.py
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
    1) This endpoint is /image/ (POST)
    2) Expects a multipart/form-data field named “file”
    3) Verifies content_type is PNG/JPEG/GIF
    4) Calls upload_image_to_supabase(...) to push bytes into Supabase
    5) Returns {"url": <public_url>}
    """
    logger.info(
        f"User {current_user.id} is uploading file "
        f"'{file.filename}' (type={file.content_type})"
    )

    if file.content_type not in {"image/png", "image/jpeg", "image/gif"}:
        logger.error("Invalid image type. Only PNG/JPEG/GIF allowed.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image type. Only PNG/JPEG/GIF allowed.",
        )

    contents = await file.read()
    logger.debug(f"Read {len(contents)} bytes from '{file.filename}'")

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
    1) This endpoint is /image/ (GET)
    2) Expects a query parameter `image_id` to identify the image
    3) Expects a query parameter `storage_bucket` to identify the storage bucket
    4) Calls get_image_url_from_supabase(...) to retrieve the public URL
    5) Returns the public URL of the image if it exists
    """
    logger.info(f"User {current_user.id} requested URL for image ID {image_id}")
    return get_image_url_from_supabase(image_id, storage_bucket, current_user)
