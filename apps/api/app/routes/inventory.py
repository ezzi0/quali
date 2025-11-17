"""Inventory endpoints"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, func

from ..deps import get_db
from ..auth import verify_optional_secret
from ..models.unit import Unit, UnitStatus

router = APIRouter()


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
    status: Optional[str] = "available",
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
    _auth: None = Depends(verify_optional_secret),
):
    """Search inventory with filters"""
    query = select(Unit)
    filters = []

    # Apply filters
    if status:
        try:
            status_enum = UnitStatus(status)
            filters.append(Unit.status == status_enum)
        except ValueError:
            pass  # Ignore invalid status

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
                "price": float(unit.price),
                "currency": unit.currency,
                "area_m2": unit.area_m2,
                "beds": unit.beds,
                "baths": unit.baths,
                "location": unit.location,
                "city": unit.city,
                "area": unit.area,
                "property_type": unit.property_type,
                "status": unit.status.value,
                "features": unit.features or [],
                "description": unit.description,
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
    _auth: None = Depends(verify_optional_secret),
):
    """Get unit details"""
    unit = db.get(Unit, unit_id)

    if not unit:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Unit not found")

    return {
        "id": unit.id,
        "title": unit.title,
        "price": float(unit.price),
        "currency": unit.currency,
        "area_m2": unit.area_m2,
        "beds": unit.beds,
        "baths": unit.baths,
        "location": unit.location,
        "city": unit.city,
        "area": unit.area,
        "property_type": unit.property_type,
        "status": unit.status.value,
        "features": unit.features or [],
        "description": unit.description,
        "created_at": unit.created_at.isoformat(),
    }
