"""Auth middleware - no-op for MVP with optional secret header"""
from fastapi import Header, HTTPException, status
from typing import Optional

from .config import get_settings

settings = get_settings()


async def verify_optional_secret(
    x_api_secret: Optional[str] = Header(None)
) -> None:
    """
    Optional secret header check.
    If APP_SECRET is set, validate incoming requests have matching header.
    Otherwise, allow all requests (no-auth MVP).
    """
    if settings.app_secret:
        if not x_api_secret or x_api_secret != settings.app_secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API secret",
            )
    # No-op if APP_SECRET not configured
    return None
