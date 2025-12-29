"""Admin-only endpoints for user management"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import httpx

from ..auth import require_super_admin, require_staff_user
from ..config import get_settings
from ..deps import get_db
from ..models.auth_user import AuthUser, UserRole

settings = get_settings()
router = APIRouter()


class InviteUserRequest(BaseModel):
    email: str
    role: str = "agent"
    redirect_to: Optional[str] = None


class UpdateRoleRequest(BaseModel):
    role: str


@router.get("/users")
async def list_users(
    db: Session = Depends(get_db),
    _user = Depends(require_super_admin),
):
    users = db.query(AuthUser).order_by(AuthUser.created_at.desc()).all()
    return {
        "users": [
            {
                "id": user.id,
                "email": user.email,
                "role": user.role.value,
                "name": user.name,
                "created_at": user.created_at.isoformat(),
            }
            for user in users
        ]
    }


@router.get("/me")
async def get_me(
    user = Depends(require_staff_user),
):
    return {
        "email": user.email,
        "role": user.role.value,
        "is_super_admin": user.email.lower() == "eli@abriqot.com",
    }


def _enforce_domain(email: str) -> None:
    if not email.lower().endswith("@abriqot.com"):
        raise HTTPException(status_code=400, detail="Email must be @abriqot.com")


def _get_supabase_headers() -> dict:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise HTTPException(status_code=500, detail="Supabase admin is not configured")
    return {
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "apikey": settings.supabase_service_role_key,
        "Content-Type": "application/json",
    }


@router.post("/users/invite")
async def invite_user(
    payload: InviteUserRequest,
    db: Session = Depends(get_db),
    _user = Depends(require_super_admin),
):
    _enforce_domain(payload.email)

    role_value = payload.role.lower()
    if role_value not in {"admin", "agent"}:
        raise HTTPException(status_code=400, detail="Invalid role")

    user = db.query(AuthUser).filter(AuthUser.email == payload.email).first()
    if not user:
        user = AuthUser(email=payload.email, role=UserRole(role_value))
        db.add(user)
    else:
        user.role = UserRole(role_value)

    db.commit()

    invite_url = f"{settings.supabase_url.rstrip('/')}/auth/v1/invite"
    body = {
        "email": payload.email,
        "redirect_to": payload.redirect_to,
    }

    try:
        response = httpx.post(invite_url, headers=_get_supabase_headers(), json=body, timeout=10)
        response.raise_for_status()
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Failed to send invite") from exc

    return {"status": "invited"}


@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    payload: UpdateRoleRequest,
    db: Session = Depends(get_db),
    _user = Depends(require_super_admin),
):
    role_value = payload.role.lower()
    if role_value not in {"admin", "agent"}:
        raise HTTPException(status_code=400, detail="Invalid role")

    user = db.get(AuthUser, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.email.lower() == "eli@abriqot.com":
        user.role = UserRole.ADMIN
    else:
        user.role = UserRole(role_value)

    db.commit()

    return {"status": "updated"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _user = Depends(require_super_admin),
):
    user = db.get(AuthUser, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.email.lower() == "eli@abriqot.com":
        raise HTTPException(status_code=400, detail="Cannot delete super admin")

    db.delete(user)
    db.commit()

    return {"status": "deleted"}
