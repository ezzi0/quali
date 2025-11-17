"""Leads endpoints"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, desc, func
from datetime import datetime

from ..deps import get_db
from ..auth import verify_optional_secret
from ..models.lead import Lead, LeadProfile, LeadStatus
from ..models.contact import Contact
from ..models.qualification import Qualification
from ..models.activity import Activity
from ..models.task import Task, TaskStatus
from ..logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class LeadResponse(BaseModel):
    """Lead response DTO"""
    id: int
    source: str
    persona: str | None
    status: str
    created_at: datetime
    contact: dict | None
    profile: dict | None
    latest_qualification: dict | None

    model_config = {"from_attributes": True}


class TaskCreate(BaseModel):
    """Task creation request"""
    title: str
    description: str | None = None
    due_at: datetime | None = None
    assignee: str | None = None


class QualifyRequest(BaseModel):
    """Manual qualification override"""
    score: int
    qualified: bool
    reasons: List[str]
    suggested_next_step: str


@router.get("")
async def list_leads(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _auth: None = Depends(verify_optional_secret),
):
    """List leads with optional filters"""
    filters = []

    query = select(Lead).options(
        joinedload(Lead.contact),
        joinedload(Lead.profile),
    ).order_by(desc(Lead.created_at))

    if status:
        try:
            status_enum = LeadStatus(status)
            filters.append(Lead.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid status: {status}")

    if filters:
        query = query.where(*filters)

    query = query.limit(limit).offset(offset)

    leads = db.execute(query).scalars().all()
    total = db.execute(
        select(func.count()).select_from(Lead).where(*filters)
        if filters
        else select(func.count()).select_from(Lead)
    ).scalar_one()

    return {
        "leads": [
            {
                "id": lead.id,
                "source": lead.source.value,
                "persona": lead.persona.value if lead.persona else None,
                "status": lead.status.value,
                "created_at": lead.created_at.isoformat(),
                "contact": {
                    "name": lead.contact.name,
                    "email": lead.contact.email,
                    "phone": lead.contact.phone,
                } if lead.contact else None,
            }
            for lead in leads
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{lead_id}")
async def get_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    _auth: None = Depends(verify_optional_secret),
):
    """Get lead detail with timeline"""
    lead = db.execute(
        select(Lead)
        .options(
            joinedload(Lead.contact),
            joinedload(Lead.profile),
        )
        .where(Lead.id == lead_id)
    ).scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Get latest qualification
    latest_qual = db.execute(
        select(Qualification)
        .where(Qualification.lead_id == lead_id)
        .order_by(desc(Qualification.created_at))
        .limit(1)
    ).scalar_one_or_none()

    # Get timeline (activities)
    activities = db.execute(
        select(Activity)
        .where(Activity.lead_id == lead_id)
        .order_by(Activity.created_at)
    ).scalars().all()

    # Get tasks
    tasks = db.execute(
        select(Task)
        .where(Task.lead_id == lead_id)
        .order_by(Task.created_at)
    ).scalars().all()

    return {
        "id": lead.id,
        "source": lead.source.value,
        "persona": lead.persona.value if lead.persona else None,
        "status": lead.status.value,
        "created_at": lead.created_at.isoformat(),
        "contact": {
            "id": lead.contact.id,
            "name": lead.contact.name,
            "email": lead.contact.email,
            "phone": lead.contact.phone,
        } if lead.contact else None,
        "profile": {
            "city": lead.profile.city,
            "areas": lead.profile.areas,
            "property_type": lead.profile.property_type,
            "beds": lead.profile.beds,
            "budget_min": float(lead.profile.budget_min) if lead.profile.budget_min else None,
            "budget_max": float(lead.profile.budget_max) if lead.profile.budget_max else None,
            "currency": lead.profile.currency,
            "move_in_date": lead.profile.move_in_date,
        } if lead.profile else None,
        "qualification": {
            "score": latest_qual.score,
            "qualified": latest_qual.qualified,
            "reasons": latest_qual.reasons,
            "missing_info": latest_qual.missing_info,
            "suggested_next_step": latest_qual.suggested_next_step,
            "top_matches": latest_qual.top_matches,
            "created_at": latest_qual.created_at.isoformat(),
        } if latest_qual else None,
        "timeline": [
            {
                "id": activity.id,
                "type": activity.type.value,
                "payload": activity.payload,
                "created_at": activity.created_at.isoformat(),
            }
            for activity in activities
        ],
        "tasks": [
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status.value,
                "due_at": task.due_at.isoformat() if task.due_at else None,
                "assignee": task.assignee,
                "created_at": task.created_at.isoformat(),
            }
            for task in tasks
        ],
    }


@router.post("/{lead_id}/tasks")
async def create_task(
    lead_id: int,
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    _auth: None = Depends(verify_optional_secret),
):
    """Create a follow-up task"""
    # Verify lead exists
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    task = Task(
        lead_id=lead_id,
        title=task_data.title,
        description=task_data.description,
        due_at=task_data.due_at,
        assignee=task_data.assignee,
        status=TaskStatus.TODO,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    logger.info("task_created", lead_id=lead_id, task_id=task.id)

    return {
        "id": task.id,
        "title": task.title,
        "status": task.status.value,
        "created_at": task.created_at.isoformat(),
    }


@router.post("/{lead_id}/qualify")
async def manual_qualify(
    lead_id: int,
    qual_data: QualifyRequest,
    db: Session = Depends(get_db),
    _auth: None = Depends(verify_optional_secret),
):
    """Manual qualification override (human-in-the-loop)"""
    # Verify lead exists
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    qualification = Qualification(
        lead_id=lead_id,
        score=qual_data.score,
        qualified=qual_data.qualified,
        reasons=qual_data.reasons,
        missing_info=[],
        suggested_next_step=qual_data.suggested_next_step,
        top_matches=None,
    )

    db.add(qualification)

    # Update lead status
    if qual_data.qualified:
        lead.status = LeadStatus.QUALIFIED

    db.commit()
    db.refresh(qualification)

    logger.info("manual_qualification", lead_id=lead_id, score=qual_data.score)

    return {
        "id": qualification.id,
        "score": qualification.score,
        "qualified": qualification.qualified,
    }
