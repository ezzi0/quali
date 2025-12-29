"""Auth middleware - optional secret header + Supabase auth for admin portal"""
from fastapi import Header, HTTPException, status, Depends
from typing import Optional
from jose import jwt, JWTError
import logging
import time
import httpx
from sqlalchemy.orm import Session

from .config import get_settings
from .deps import get_db
from .models.auth_user import AuthUser, UserRole

settings = get_settings()
logger = logging.getLogger(__name__)

_JWKS_CACHE: dict[str, object] = {"keys": None, "expires": 0.0}


def _get_supabase_jwks() -> list[dict]:
    if not settings.supabase_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase URL is not configured",
        )

    now = time.time()
    if _JWKS_CACHE["keys"] and now < float(_JWKS_CACHE["expires"]):
        return _JWKS_CACHE["keys"]  # type: ignore[return-value]

    jwks_url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
    headers = {}
    if settings.supabase_service_role_key:
        headers = {
            "Authorization": f"Bearer {settings.supabase_service_role_key}",
            "apikey": settings.supabase_service_role_key,
        }
    try:
        response = httpx.get(jwks_url, headers=headers or None, timeout=10)
        response.raise_for_status()
        keys = response.json().get("keys", [])
        _JWKS_CACHE["keys"] = keys
        _JWKS_CACHE["expires"] = now + 3600
        return keys
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to load auth keys",
        ) from exc


def _decode_supabase_token(token: str) -> dict:
    token_alg = None
    token_kid = None
    try:
        header = jwt.get_unverified_header(token)
        token_alg = header.get("alg")
        token_kid = header.get("kid")
        jwks = _get_supabase_jwks()
        key = next((k for k in jwks if k.get("kid") == token_kid), None)
        if not key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token key",
            )

        issuer = f"{settings.supabase_url.rstrip('/')}/auth/v1"
        allowed_algs = ["RS256", "ES256"]
        key_alg = key.get("alg")
        if key_alg and key_alg not in allowed_algs:
            allowed_algs.append(key_alg)
        return jwt.decode(
            token,
            key,
            algorithms=allowed_algs,
            audience=settings.supabase_jwt_audience,
            issuer=issuer,
        )
    except JWTError as exc:
        logger.warning(
            "JWT decode failed (%s): %s (alg=%s kid=%s key_alg=%s key_kty=%s key_crv=%s aud=%s iss=%s)",
            exc.__class__.__name__,
            exc,
            token_alg,
            token_kid,
            key.get("alg") if "key" in locals() and key else None,
            key.get("kty") if "key" in locals() and key else None,
            key.get("crv") if "key" in locals() and key else None,
            settings.supabase_jwt_audience,
            issuer,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc


def _enforce_domain(email: str) -> None:
    if not email.lower().endswith("@abriqot.com"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to abriqot.com accounts",
        )


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
    return None


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> AuthUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    token = authorization.split(" ", 1)[1].strip()
    payload = _decode_supabase_token(token)

    email = payload.get("email") or payload.get("user_metadata", {}).get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not found in token",
        )

    _enforce_domain(email)

    user = db.query(AuthUser).filter(AuthUser.email == email).first()
    if not user:
        if email.lower() == "eli@abriqot.com":
            user = AuthUser(email=email, role=UserRole.ADMIN, name="Eli")
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not invited",
            )
    return user


async def require_staff_user(
    user: AuthUser = Depends(get_current_user),
) -> AuthUser:
    return user


async def require_admin_user(
    user: AuthUser = Depends(get_current_user),
) -> AuthUser:
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


async def require_super_admin(
    user: AuthUser = Depends(get_current_user),
) -> AuthUser:
    if user.email.lower() != "eli@abriqot.com":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required",
        )
    return user
