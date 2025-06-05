import uuid
import logging
from fastapi import HTTPException, status
from storage3.exceptions import StorageApiError
from supabase_client import supabase

logger = logging.getLogger(__name__)

def upload_image_to_supabase(contents: bytes, original_filename: str) -> str:
    """
    1) Build a unique file path under “memes/” using a UUID + original extension.
    2) Call supabase.storage.from_("memes").upload(...). If it fails, StorageApiError is raised.
    3) Call get_public_url(...) which may return either:
       - a plain string, or 
       - a dict containing {"publicURL": "<url>"}.
    4) Normalize and return a string URL, or raise HTTPException if something went wrong.
    """

    # Step 1: Build a unique filename
    try:
        suffix = original_filename.rsplit(".", 1)[1].lower()
    except Exception:
        suffix = "png"
    object_path = f"memes/{uuid.uuid4().hex}.{suffix}"

    # Step 2: Attempt the upload
    try:
        supabase.storage.from_("memes").upload(object_path, contents)
    except StorageApiError as e:
        msg = str(e)
        logger.error(f"Supabase upload failed: {msg}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Supabase storage upload failed: {msg}"
        )

    # Step 3: Retrieve the public URL
    url_resp = supabase.storage.from_("memes").get_public_url(object_path)

    # Step 4: Normalize whatever get_public_url returned into a single string
    if isinstance(url_resp, str):
        # Newer versions of supabase-py simply return the URL string
        public_url = url_resp
    else:
        # Older versions returned a dict, e.g. {"publicURL": "..."}
        public_url = url_resp.get("publicURL") if isinstance(url_resp, dict) else None

    if not public_url:
        logger.error(f"Could not retrieve public URL after upload: {url_resp!r}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve public URL after upload."
        )

    return public_url