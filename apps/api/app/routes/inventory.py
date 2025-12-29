"""Inventory endpoints"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, func, or_
import re

from ..deps import get_db
from ..auth import require_staff_user
from ..models.unit import Unit, UnitStatus

router = APIRouter()


class UnitCreate(BaseModel):
    """Create inventory unit"""
    title: str
    slug: Optional[str] = None
    developer: Optional[str] = None
    image_url: Optional[str] = None
    price: float
    currency: str = "AED"
    price_display: Optional[str] = None
    payment_plan: Optional[str] = None
    area_m2: Optional[int] = None
    beds: Optional[int] = None
    baths: Optional[int] = None
    bedrooms_label: Optional[str] = None
    unit_sizes: Optional[str] = None
    location: str
    city: Optional[str] = None
    area: Optional[str] = None
    property_type: str
    status: Optional[str] = "available"
    features: Optional[List[str]] = None
    description: Optional[str] = None
    handover: Optional[str] = None
    handover_year: Optional[int] = None
    roi: Optional[str] = None
    active: bool = True
    featured: bool = False


class UnitUpdate(BaseModel):
    """Update inventory unit"""
    title: Optional[str] = None
    slug: Optional[str] = None
    developer: Optional[str] = None
    image_url: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    price_display: Optional[str] = None
    payment_plan: Optional[str] = None
    area_m2: Optional[int] = None
    beds: Optional[int] = None
    baths: Optional[int] = None
    bedrooms_label: Optional[str] = None
    unit_sizes: Optional[str] = None
    location: Optional[str] = None
    city: Optional[str] = None
    area: Optional[str] = None
    property_type: Optional[str] = None
    status: Optional[str] = None
    features: Optional[List[str]] = None
    description: Optional[str] = None
    handover: Optional[str] = None
    handover_year: Optional[int] = None
    roi: Optional[str] = None
    active: Optional[bool] = None
    featured: Optional[bool] = None


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value[:200] if value else "property"


def format_price_display(price: float, currency: str) -> str:
    if price >= 1_000_000:
        return f"{currency} {price / 1_000_000:.1f}M"
    if price >= 1_000:
        return f"{currency} {price / 1_000:.0f}K"
    return f"{currency} {price:,.0f}"


def parse_status(value: Optional[str]) -> Optional[UnitStatus]:
    if value is None:
        return None
    try:
        return UnitStatus(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid unit status") from exc


def normalize_image_url(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    trimmed = value.strip()
    if trimmed.startswith("http://") or trimmed.startswith("https://"):
        return trimmed
    return trimmed if trimmed.startswith("/") else f"/{trimmed}"


@router.get("/search")
async def search_inventory(
    city: Optional[str] = None,
    area: Optional[str] = None,
    property_type: Optional[str] = None,
    beds: Optional[int] = None,
    min_beds: Optional[int] = None,
    max_beds: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_area_m2: Optional[int] = None,
    status: Optional[str] = None,
    active: Optional[bool] = True,
    featured: Optional[bool] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Search inventory with filters"""
    query = select(Unit)
    filters = []

    # Apply filters
    if status and status != "all":
        status_enum = parse_status(status)
        if status_enum:
            filters.append(Unit.status == status_enum)

    if active is not None:
        filters.append(Unit.active == active)

    if featured is not None:
        filters.append(Unit.featured == featured)

    if city:
        filters.append(Unit.city.ilike(f"%{city}%"))

    if area:
        filters.append(Unit.area.ilike(f"%{area}%"))

    if property_type:
        filters.append(Unit.property_type.ilike(f"%{property_type}%"))

    if beds is not None:
        filters.append(Unit.beds == beds)
    else:
        if min_beds is not None:
            filters.append(Unit.beds >= min_beds)
        if max_beds is not None:
            filters.append(Unit.beds <= max_beds)

    if min_price is not None:
        filters.append(Unit.price >= min_price)

    if max_price is not None:
        filters.append(Unit.price <= max_price)

    if min_area_m2 is not None:
        filters.append(Unit.area_m2 >= min_area_m2)

    if filters:
        query = query.where(*filters)

    # Order and paginate
    query = query.order_by(desc(Unit.created_at)).limit(limit).offset(offset)

    units = db.execute(query).scalars().all()
    total = db.execute(
        select(func.count()).select_from(Unit).where(*filters)
        if filters
        else select(func.count()).select_from(Unit)
    ).scalar_one()

    return {
        "units": [
            {
                "id": unit.id,
                "title": unit.title,
                "slug": unit.slug,
                "developer": unit.developer,
                "image_url": unit.image_url,
                "price": float(unit.price),
                "currency": unit.currency,
                "price_display": unit.price_display,
                "payment_plan": unit.payment_plan,
                "area_m2": unit.area_m2,
                "beds": unit.beds,
                "baths": unit.baths,
                "bedrooms_label": unit.bedrooms_label,
                "unit_sizes": unit.unit_sizes,
                "location": unit.location,
                "city": unit.city,
                "area": unit.area,
                "property_type": unit.property_type,
                "status": unit.status.value,
                "active": unit.active,
                "featured": unit.featured,
                "handover": unit.handover,
                "handover_year": unit.handover_year,
                "roi": unit.roi,
                "features": unit.features or [],
                "description": unit.description,
            }
            for unit in units
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/admin")
async def list_inventory_admin(
    q: Optional[str] = None,
    status: Optional[str] = None,
    active: Optional[bool] = None,
    featured: Optional[bool] = None,
    limit: int = Query(100, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
    _user = Depends(require_staff_user),
):
    """Admin inventory list with optional filters"""
    query = select(Unit)
    filters = []

    if status and status != "all":
        status_enum = parse_status(status)
        if status_enum:
            filters.append(Unit.status == status_enum)

    if active is not None:
        filters.append(Unit.active == active)

    if featured is not None:
        filters.append(Unit.featured == featured)

    if q:
        like = f"%{q}%"
        filters.append(
            or_(
                Unit.title.ilike(like),
                Unit.developer.ilike(like),
                Unit.location.ilike(like),
                Unit.city.ilike(like),
                Unit.area.ilike(like),
            )
        )

    if filters:
        query = query.where(*filters)

    query = query.order_by(desc(Unit.created_at)).limit(limit).offset(offset)

    units = db.execute(query).scalars().all()
    total = db.execute(
        select(func.count()).select_from(Unit).where(*filters)
        if filters
        else select(func.count()).select_from(Unit)
    ).scalar_one()

    return {
        "units": [
            {
                "id": unit.id,
                "title": unit.title,
                "slug": unit.slug,
                "developer": unit.developer,
                "image_url": unit.image_url,
                "price": float(unit.price),
                "currency": unit.currency,
                "price_display": unit.price_display,
                "payment_plan": unit.payment_plan,
                "area_m2": unit.area_m2,
                "beds": unit.beds,
                "baths": unit.baths,
                "bedrooms_label": unit.bedrooms_label,
                "unit_sizes": unit.unit_sizes,
                "location": unit.location,
                "city": unit.city,
                "area": unit.area,
                "property_type": unit.property_type,
                "status": unit.status.value,
                "active": unit.active,
                "featured": unit.featured,
                "handover": unit.handover,
                "handover_year": unit.handover_year,
                "roi": unit.roi,
                "features": unit.features or [],
                "description": unit.description,
                "created_at": unit.created_at.isoformat(),
            }
            for unit in units
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{unit_id}")
async def get_unit(
    unit_id: int,
    db: Session = Depends(get_db),
):
    """Get unit details"""
    unit = db.get(Unit, unit_id)

    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    return {
        "id": unit.id,
        "title": unit.title,
        "slug": unit.slug,
        "developer": unit.developer,
        "image_url": unit.image_url,
        "price": float(unit.price),
        "currency": unit.currency,
        "price_display": unit.price_display,
        "payment_plan": unit.payment_plan,
        "area_m2": unit.area_m2,
        "beds": unit.beds,
        "baths": unit.baths,
        "bedrooms_label": unit.bedrooms_label,
        "unit_sizes": unit.unit_sizes,
        "location": unit.location,
        "city": unit.city,
        "area": unit.area,
        "property_type": unit.property_type,
        "status": unit.status.value,
        "active": unit.active,
        "featured": unit.featured,
        "handover": unit.handover,
        "handover_year": unit.handover_year,
        "roi": unit.roi,
        "features": unit.features or [],
        "description": unit.description,
        "created_at": unit.created_at.isoformat(),
    }


@router.get("/slug/{slug}")
async def get_unit_by_slug(
    slug: str,
    db: Session = Depends(get_db),
):
    """Get unit details by slug"""
    unit = db.execute(select(Unit).where(Unit.slug == slug)).scalars().first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    return {
        "id": unit.id,
        "title": unit.title,
        "slug": unit.slug,
        "developer": unit.developer,
        "image_url": unit.image_url,
        "price": float(unit.price),
        "currency": unit.currency,
        "price_display": unit.price_display,
        "payment_plan": unit.payment_plan,
        "area_m2": unit.area_m2,
        "beds": unit.beds,
        "baths": unit.baths,
        "bedrooms_label": unit.bedrooms_label,
        "unit_sizes": unit.unit_sizes,
        "location": unit.location,
        "city": unit.city,
        "area": unit.area,
        "property_type": unit.property_type,
        "status": unit.status.value,
        "active": unit.active,
        "featured": unit.featured,
        "handover": unit.handover,
        "handover_year": unit.handover_year,
        "roi": unit.roi,
        "features": unit.features or [],
        "description": unit.description,
        "created_at": unit.created_at.isoformat(),
    }


@router.post("")
async def create_unit(
    payload: UnitCreate,
    db: Session = Depends(get_db),
    _user = Depends(require_staff_user),
):
    """Create a new unit"""
    status_enum = parse_status(payload.status) or UnitStatus.AVAILABLE
    slug = payload.slug.strip() if payload.slug else None
    if not slug:
        slug = slugify(payload.title)

    price_display = payload.price_display
    if not price_display:
        price_display = format_price_display(payload.price, payload.currency)

    unit = Unit(
        title=payload.title,
        slug=slug,
        developer=payload.developer,
        image_url=normalize_image_url(payload.image_url),
        price=payload.price,
        currency=payload.currency,
        price_display=price_display,
        payment_plan=payload.payment_plan,
        area_m2=payload.area_m2,
        beds=payload.beds,
        baths=payload.baths,
        bedrooms_label=payload.bedrooms_label,
        unit_sizes=payload.unit_sizes,
        location=payload.location,
        city=payload.city,
        area=payload.area,
        property_type=payload.property_type,
        status=status_enum,
        features=payload.features or [],
        description=payload.description,
        handover=payload.handover,
        handover_year=payload.handover_year,
        roi=payload.roi,
        active=payload.active,
        featured=payload.featured,
    )
    db.add(unit)
    db.commit()
    db.refresh(unit)

    return {"id": unit.id}


@router.put("/{unit_id}")
async def update_unit(
    unit_id: int,
    payload: UnitUpdate,
    db: Session = Depends(get_db),
    _user = Depends(require_staff_user),
):
    """Update a unit"""
    unit = db.get(Unit, unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    status_enum = parse_status(payload.status) if payload.status is not None else None

    update_data = payload.model_dump(exclude_unset=True)
    if "status" in update_data:
        update_data["status"] = status_enum

    if "slug" in update_data:
        slug = update_data["slug"]
        update_data["slug"] = slugify(slug) if slug else slugify(payload.title or unit.title)

    if "price" in update_data and "price_display" not in update_data:
        update_data["price_display"] = format_price_display(
            update_data["price"], update_data.get("currency", unit.currency)
        )

    if "image_url" in update_data:
        update_data["image_url"] = normalize_image_url(update_data["image_url"])

    for key, value in update_data.items():
        setattr(unit, key, value)

    db.commit()
    db.refresh(unit)

    return {"id": unit.id}


@router.delete("/{unit_id}")
async def delete_unit(
    unit_id: int,
    db: Session = Depends(get_db),
    _user = Depends(require_staff_user),
):
    """Delete a unit"""
    unit = db.get(Unit, unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    db.delete(unit)
    db.commit()

    return {"status": "deleted"}
