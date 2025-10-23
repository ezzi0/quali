"""Webhook endpoints for Lead Ads and WhatsApp"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..deps import get_db, get_redis
from ..auth import verify_optional_secret
from ..models.lead import Lead, LeadSource, LeadStatus
from ..models.contact import Contact
from ..models.activity import Activity, ActivityType
from ..logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/leadads")
async def lead_ads_webhook(
    request: Request,
    db: Session = Depends(get_db),
    _auth: None = Depends(verify_optional_secret),
):
    """
    Meta Lead Ads webhook handler.

    In production:
    - Verify webhook signature
    - Handle verification challenge
    - Parse lead form data
    - Dedupe based on email/phone
    """
    try:
        payload = await request.json()

        # Verification challenge (Meta setup)
        if "hub.mode" in payload and payload.get("hub.mode") == "subscribe":
            challenge = payload.get("hub.challenge")
            return {"hub.challenge": challenge}

        # Process lead ad
        # (Simplified - production would parse Meta's nested structure)
        entry = payload.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})

        leadgen_id = value.get("leadgen_id")
        form_data = value.get("form_data", {})

        # Extract contact info
        email = None
        phone = None
        name = None

        for field in form_data.get("field_data", []):
            if field.get("name") == "email":
                email = field.get("values", [None])[0]
            elif field.get("name") == "phone_number":
                phone = field.get("values", [None])[0]
            elif field.get("name") == "full_name":
                name = field.get("values", [None])[0]

        # Create or get contact
        contact = None
        if email or phone:
            # Simple dedupe check
            from sqlalchemy import select, or_
            existing = db.execute(
                select(Contact).where(
                    or_(
                        Contact.email == email if email else False,
                        Contact.phone == phone if phone else False,
                    )
                )
            ).scalar_one_or_none()

            if existing:
                contact = existing
            else:
                contact = Contact(
                    name=name,
                    email=email,
                    phone=phone,
                    consent_email=True if email else False,
                )
                db.add(contact)
                db.flush()

        # Create lead
        lead = Lead(
            source=LeadSource.LEAD_AD,
            status=LeadStatus.NEW,
            contact_id=contact.id if contact else None,
        )
        db.add(lead)
        db.flush()

        # Log activity
        activity = Activity(
            lead_id=lead.id,
            type=ActivityType.MESSAGE,
            payload={
                "source": "lead_ad",
                "leadgen_id": leadgen_id,
                "form_data": form_data,
            },
        )
        db.add(activity)

        db.commit()

        logger.info("lead_ad_ingested", lead_id=lead.id,
                    contact_id=contact.id if contact else None)

        # TODO: Enqueue agent qualification job

        return {"success": True, "lead_id": lead.id}

    except Exception as e:
        logger.error("lead_ad_webhook_failed", error=str(e))
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/whatsapp")
async def whatsapp_webhook(
    request: Request,
    db: Session = Depends(get_db),
    _auth: None = Depends(verify_optional_secret),
):
    """
    WhatsApp webhook handler for incoming messages and Flow completions.

    In production:
    - Verify webhook signature
    - Handle verification challenge
    - Parse Flow payload
    - Route messages to appropriate handler
    """
    try:
        payload = await request.json()

        # Verification challenge (Meta setup)
        if "hub.mode" in payload and payload.get("hub.mode") == "subscribe":
            challenge = payload.get("hub.challenge")
            return {"hub.challenge": challenge}

        # Process WhatsApp message/Flow
        entry = payload.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})

        messages = value.get("messages", [])

        for message in messages:
            msg_from = message.get("from")
            msg_type = message.get("type")

            # Handle Flow completion
            if msg_type == "interactive" and message.get("interactive", {}).get("type") == "nfm_reply":
                flow_response = message.get(
                    "interactive", {}).get("nfm_reply", {})
                response_json = flow_response.get("response_json", {})

                # Parse Flow data (intake form)
                # (Structure depends on your Flow design)

                # Create/update lead
                # For now, just log it
                logger.info("whatsapp_flow_completed",
                            phone=msg_from, data=response_json)

                return {"success": True}

            # Handle regular message
            elif msg_type == "text":
                text = message.get("text", {}).get("body", "")

                # Find or create lead by phone
                from sqlalchemy import select
                contact = db.execute(
                    select(Contact).where(Contact.phone == msg_from)
                ).scalar_one_or_none()

                if not contact:
                    contact = Contact(phone=msg_from, consent_whatsapp=True)
                    db.add(contact)
                    db.flush()

                # Find or create lead
                lead = db.execute(
                    select(Lead).where(Lead.contact_id == contact.id)
                ).scalar_one_or_none()

                if not lead:
                    lead = Lead(
                        source=LeadSource.WHATSAPP,
                        status=LeadStatus.NEW,
                        contact_id=contact.id,
                    )
                    db.add(lead)
                    db.flush()

                # Log activity
                activity = Activity(
                    lead_id=lead.id,
                    type=ActivityType.WHATSAPP,
                    payload={"message": text, "from": msg_from},
                )
                db.add(activity)

                db.commit()

                logger.info("whatsapp_message_received",
                            lead_id=lead.id, phone=msg_from)

                # TODO: Enqueue agent response job

        return {"success": True}

    except Exception as e:
        logger.error("whatsapp_webhook_failed", error=str(e))
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
