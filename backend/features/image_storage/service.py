# backend/features/image_storage/service.py
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
    1) Build a unique file path under “<storage_bucket>/” using a UUID + original extension.
    2) Call supabase.storage.from_("<storage_bucket>").upload(...). If it fails, StorageApiError is raised.
    3) Call get_public_url(...) which may return either:
       - a plain string, or
       - a dict containing {"publicURL": "<url>"}.
    4) Normalize and return a string URL, or raise HTTPException if something went wrong.
    """

    # Step 1: Build a unique filename
    # try:
    #     suffix = original_filename.rsplit(".", 1)[1].lower()
    # except Exception:
    #     suffix = "png"
    # file_name = f"{uuid.uuid4().hex}.{suffix}"
    # logger.info(f"Generated object file name: {file_name}")
    file_name = original_filename

    # Step 2: Attempt the upload
    try:
        logger.info(f"Uploading {original_filename} to Supabase at {file_name}")
        supabase.storage.from_(storage_bucket).upload(
            file_name, contents, file_options={"content-type": content_type}
        )
        logger.info(f"Upload successful for {file_name}")
    except StorageApiError as e:
        msg = str(e)
        logger.error(f"Supabase upload failed: {msg}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Supabase storage upload failed: {msg}",
        )

    # Step 3: Retrieve the public URL
    logger.info(f"Retrieving public URL for {file_name}")
    url_resp = supabase.storage.from_(storage_bucket).get_public_url(file_name)

    # Step 4: Normalize whatever get_public_url returned into a single string
    if isinstance(url_resp, str):
        public_url = url_resp
        logger.debug(f"get_public_url returned string: {public_url}")
    else:
        public_url = url_resp.get("publicURL") if isinstance(url_resp, dict) else None
        logger.debug(f"get_public_url returned dict: {url_resp!r}")

    if not public_url:
        logger.error(f"Could not retrieve public URL after upload: {url_resp!r}")
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
    1) Calls supabase.storage.from_(storage_bucket).get_public_url(image_id)
    2) Returns the public URL of the image if it exists
    3) Raises HTTPException if the image does not exist or any other error occurs
    """
    logger.info(f"User {current_user.id} requested URL for image ID {image_id}")

    try:
        url_resp = supabase.storage.from_(storage_bucket).get_public_url(image_id)
        if isinstance(url_resp, str):
            public_url = url_resp
        else:
            public_url = url_resp.get("publicURL", None)

        if not public_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image with ID {image_id} not found in bucket {storage_bucket}.",
            )

        logger.info(f"Returning public URL: {public_url}")
        return public_url

    except StorageApiError as e:
        msg = str(e)
        logger.error(f"Failed to retrieve image URL: {msg}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve image URL: {msg}",
        )
