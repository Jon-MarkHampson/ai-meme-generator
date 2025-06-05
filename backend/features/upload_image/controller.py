from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from ..auth.service import get_current_user
from entities.user import User
from .service import upload_image_to_supabase

router = APIRouter(prefix="/upload-image", tags=["upload-image"])

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Upload an image for the authenticated user",
)
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    1) This endpoint is /upload-image/ (POST)
    2) Expects a multipart/form-data field named “file”
    3) Verifies content_type is PNG/JPEG/GIF
    4) Calls upload_image_to_supabase(...) to push bytes into Supabase
    5) Returns {"url": <public_url>}
    """
    if file.content_type not in {"image/png", "image/jpeg", "image/gif"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image type. Only PNG/JPEG/GIF allowed.",
        )

    contents = await file.read()
    public_url = upload_image_to_supabase(contents, file.filename)
    return {"url": public_url}