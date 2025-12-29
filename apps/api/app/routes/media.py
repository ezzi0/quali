"""Media upload endpoints"""
from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from ..auth import require_staff_user
from ..config import get_settings

router = APIRouter()
settings = get_settings()

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_UPLOAD_BYTES = 8 * 1024 * 1024  # 8MB


@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    _user=Depends(require_staff_user),
):
    """Upload an image to Supabase Storage and return the public URL"""
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase storage is not configured",
        )

    if not file.content_type or file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type",
        )

    extension = ALLOWED_CONTENT_TYPES[file.content_type]
    filename = f"{uuid4().hex}{extension}"

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large",
        )

    bucket = settings.supabase_storage_bucket
    upload_url = f"{settings.supabase_url.rstrip('/')}/storage/v1/object/{bucket}/{filename}"
    headers = {
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "apikey": settings.supabase_service_role_key,
        "Content-Type": file.content_type,
        "x-upsert": "true",
    }

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(upload_url, headers=headers, content=contents)

    if response.status_code not in (200, 201):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Upload failed: {response.text}",
        )

    public_url = f"{settings.supabase_url.rstrip('/')}/storage/v1/object/public/{bucket}/{filename}"
    return {
        "url": public_url,
        "filename": filename,
        "size": len(contents),
    }
