"""Agent tools for OpenAI Agents SDK"""
import re
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..models.unit import Unit, UnitStatus
from ..models.lead import Lead, LeadProfile, LeadPersona, LeadStatus
from ..models.qualification import Qualification
from ..models.contact import Contact
from .scoring import lead_scorer
from ..logging import get_logger

logger = get_logger(__name__)


def inventory_search(
    db: Session,
    criteria: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Search inventory based on criteria.
    Returns top matching units.
    If no exact matches, tries with relaxed criteria (e.g., +/- 2 beds, higher price range).
    """
    def build_query(criteria_dict, exact_beds=True):
        query = select(Unit).where(Unit.status == UnitStatus.AVAILABLE)

        if location := criteria_dict.get("location"):
            query = query.where(Unit.location.ilike(f"%{location}%"))

        if city := criteria_dict.get("city"):
            query = query.where(Unit.city.ilike(f"%{city}%"))

        if area := criteria_dict.get("area"):
            query = query.where(Unit.area.ilike(f"%{area}%"))

        if property_type := criteria_dict.get("property_type"):
            query = query.where(Unit.property_type.ilike(f"%{property_type}%"))

        if beds := criteria_dict.get("beds"):
            if exact_beds:
                query = query.where(Unit.beds == beds)
            else:
                # Relaxed: +/- 2 bedrooms
                query = query.where(Unit.beds.between(max(1, beds - 2), beds + 2))

        if min_price := criteria_dict.get("min_price"):
            query = query.where(Unit.price >= min_price)

        if max_price := criteria_dict.get("max_price"):
            query = query.where(Unit.price <= max_price)

        if min_area_m2 := criteria_dict.get("min_area_m2"):
            query = query.where(Unit.area_m2 >= min_area_m2)

        query = query.limit(criteria_dict.get("limit", 20))
        return query

    # Try exact match first
    query = build_query(criteria, exact_beds=True)
    units = db.execute(query).scalars().all()

    # If no results and beds specified, try relaxed bedroom count
    if not units and criteria.get("beds"):
        logger.info("no_exact_match_trying_relaxed_beds", original_beds=criteria.get("beds"))
        query = build_query(criteria, exact_beds=False)
        units = db.execute(query).scalars().all()

    # If still no results, try with just area + property_type (ignore beds/price)
    if not units and (criteria.get("area") or criteria.get("city")) and criteria.get("property_type"):
        logger.info("trying_area_property_type_only")
        relaxed_criteria = {
            "city": criteria.get("city"),
            "area": criteria.get("area"),
            "property_type": criteria.get("property_type"),
            "limit": criteria.get("limit", 5)
        }
        query = build_query(relaxed_criteria, exact_beds=False)
        units = db.execute(query).scalars().all()

    # Last resort: just property type in the city
    if not units and criteria.get("city") and criteria.get("property_type"):
        logger.info("trying_property_type_only")
        relaxed_criteria = {
            "city": criteria.get("city"),
            "property_type": criteria.get("property_type"),
            "limit": criteria.get("limit", 5)
        }
        query = build_query(relaxed_criteria, exact_beds=False)
        units = db.execute(query).scalars().all()

    return [
        {
            "unit_id": unit.id,
            "title": unit.title,
            "price": float(unit.price),
            "currency": unit.currency,
            "area_m2": unit.area_m2,
            "beds": unit.beds,
            "location": unit.location,
            "property_type": unit.property_type,
            "features": unit.features or [],
        }
        for unit in units
    ]


def normalize_budget(text_or_range: str) -> Dict[str, Any]:
    """
    Parse and normalize budget from text.
    Returns {min, max, currency}
    """
    # Remove common words
    text = text_or_range.lower().replace(",", "")

    # Default currency
    currency = "AED"
    if "usd" in text or "$" in text:
        currency = "USD"

    # Extract numbers
    numbers = re.findall(r'\d+(?:\.\d+)?', text)

    if not numbers:
        return {"min": None, "max": None, "currency": currency}

    # Convert to floats
    values = [float(n) for n in numbers]

    # Handle k/m multipliers
    if "k" in text:
        values = [v * 1000 if v < 1000 else v for v in values]
    if "m" in text or "million" in text:
        values = [v * 1000000 if v < 10000 else v for v in values]

    if len(values) == 1:
        # Single number - treat as max
        return {"min": 0, "max": values[0], "currency": currency}
    else:
        # Range
        return {
            "min": min(values),
            "max": max(values),
            "currency": currency,
        }


def geo_match(city: str, areas: List[str]) -> List[str]:
    """
    Validate and normalize geographic areas.
    Returns valid area list.
    (Stub - in production, match against DB or API)
    """
    # For MVP, just clean and return
    valid_areas = [area.strip().title() for area in areas if area.strip()]
    return valid_areas[:10]  # Limit to 10 areas


def save_lead_profile(
    db: Session,
    lead_id: int,
    contact: Dict[str, Any],
    profile: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Create/update contact and lead profile in the database.
    Returns confirmation with contact_id and profile_id.
    """
    try:
        # 1. Create or update Contact
        contact_obj = None
        email = contact.get("email")
        phone = contact.get("phone")
        
        # Try to find existing contact by email or phone
        if email:
            contact_obj = db.query(Contact).filter(Contact.email == email).first()
        if not contact_obj and phone:
            contact_obj = db.query(Contact).filter(Contact.phone == phone).first()
        
        if contact_obj:
            # Update existing contact
            contact_obj.name = contact.get("name", contact_obj.name)
            contact_obj.email = contact.get("email", contact_obj.email)
            contact_obj.phone = contact.get("phone", contact_obj.phone)
            contact_obj.consent_email = contact.get("consent_email", contact_obj.consent_email)
            contact_obj.consent_sms = contact.get("consent_sms", contact_obj.consent_sms)
            contact_obj.consent_whatsapp = contact.get("consent_whatsapp", contact_obj.consent_whatsapp)
            logger.info("contact_updated", contact_id=contact_obj.id)
        else:
            # Create new contact
            contact_obj = Contact(
                name=contact.get("name"),
                email=contact.get("email"),
                phone=contact.get("phone"),
                consent_email=contact.get("consent_email", False),
                consent_sms=contact.get("consent_sms", False),
                consent_whatsapp=contact.get("consent_whatsapp", False),
            )
            db.add(contact_obj)
            db.flush()  # Get the ID
            logger.info("contact_created", contact_id=contact_obj.id)
        
        # 2. Update Lead with contact
        lead = db.get(Lead, lead_id)
        if lead:
            lead.contact_id = contact_obj.id
            # Set persona if provided
            persona_str = profile.get("persona", "").lower()
            if persona_str in ["buyer", "renter", "seller"]:
                lead.persona = LeadPersona(persona_str)
        
        # 3. Create or update LeadProfile
        profile_obj = db.query(LeadProfile).filter(LeadProfile.lead_id == lead_id).first()
        
        profile_data = {
            "city": profile.get("city"),
            "areas": profile.get("areas", []),
            "property_type": profile.get("property_type"),
            "beds": profile.get("beds"),
            "min_size_m2": profile.get("min_size_m2"),
            "budget_min": profile.get("budget_min"),
            "budget_max": profile.get("budget_max"),
            "move_in_date": profile.get("move_in_date"),
            "preapproved": profile.get("preapproved"),
            "financing_notes": profile.get("financing_notes"),
            "preferences": profile.get("preferences", []),
        }
        
        if profile_obj:
            # Update existing profile
            for key, value in profile_data.items():
                if value is not None:  # Only update non-None values
                    setattr(profile_obj, key, value)
            logger.info("profile_updated", lead_id=lead_id)
        else:
            # Create new profile
            profile_obj = LeadProfile(
                lead_id=lead_id,
                **profile_data
            )
            db.add(profile_obj)
            logger.info("profile_created", lead_id=lead_id)
        
        db.commit()
        
        return {
            "success": True,
            "contact_id": contact_obj.id,
            "profile_id": profile_obj.id,
            "message": f"Saved contact {contact_obj.name} and profile for lead {lead_id}"
        }
        
    except Exception as e:
        db.rollback()
        logger.error("save_lead_profile_failed", lead_id=lead_id, error=str(e))
        return {"success": False, "error": str(e)}


def lead_score(
    profile: Dict[str, Any],
    top_matches: List[Dict[str, Any]],
    contact: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Score a lead based on profile, matches, and contact info.
    Returns {score, reasons, qualified, high_score}
    
    Scoring thresholds:
    - >= 65: High-quality lead (immediate handoff to specialist)
    - >= 50: Qualified (standard follow-up)
    - < 50: Nurture
    """
    score, reasons = lead_scorer.score_lead(profile, top_matches, contact)

    return {
        "score": score,
        "reasons": reasons,
        "qualified": score >= 50,  # Basic qualification threshold
        "high_score": score >= 65,  # High-priority handoff threshold
    }


def persist_qualification(
    db: Session,
    lead_id: int,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Persist qualification result to database.
    Handles:
    - Saving qualification record
    - Updating lead status
    - High-score lead handoff (>= 65)
    - Sending email recap
    
    Returns confirmation.
    """
    try:
        score = payload["score"]
        qualified = payload["qualified"]
        
        qualification = Qualification(
            lead_id=lead_id,
            score=score,
            qualified=qualified,
            reasons=payload["reasons"],
            missing_info=payload.get("missing_info", []),
            suggested_next_step=payload["suggested_next_step"],
            top_matches={"matches": payload.get("top_matches", [])},
        )

        db.add(qualification)

        # Update lead status based on score
        lead = db.get(Lead, lead_id)
        if lead:
            if score >= 65:
                # High-quality lead - mark as qualified and ready for handoff
                lead.status = LeadStatus.QUALIFIED
                logger.info("high_score_lead_qualified", lead_id=lead_id, score=score)
            elif qualified:
                # Medium-quality but qualified
                lead.status = LeadStatus.QUALIFIED
            else:
                # Low-quality - nurture
                lead.status = LeadStatus.NURTURE

        db.commit()

        # Send email recap if contact has email
        email_sent = False
        if lead and lead.contact and lead.contact.email and lead.contact.consent_email:
            try:
                _send_qualification_recap_email(
                    lead=lead,
                    qualification=qualification,
                    payload=payload
                )
                email_sent = True
                logger.info("recap_email_sent", lead_id=lead_id, email=lead.contact.email)
            except Exception as email_error:
                logger.error("recap_email_failed", lead_id=lead_id, error=str(email_error))

        logger.info(
            "qualification_persisted",
            lead_id=lead_id,
            score=score,
            qualified=qualified,
            high_score=score >= 65,
            email_sent=email_sent,
        )

        return {
            "success": True,
            "qualification_id": qualification.id,
            "score": score,
            "high_score": score >= 65,
            "email_sent": email_sent,
            "message": f"Qualification saved. Score: {score}/100. {'High-priority lead - will be contacted by specialist within 24 hours.' if score >= 65 else 'Lead qualified and will be reviewed.'}"
        }

    except Exception as e:
        db.rollback()
        logger.error("qualification_persist_failed",
                     lead_id=lead_id, error=str(e))
        return {"success": False, "error": str(e)}


def _send_qualification_recap_email(
    lead: Lead,
    qualification: Qualification,
    payload: Dict[str, Any]
) -> None:
    """
    Send qualification recap email to the lead.
    
    For MVP, this logs the email content.
    In production, integrate with SendGrid/AWS SES/etc.
    """
    contact = lead.contact
    profile = lead.profile
    
    if not contact or not contact.email:
        logger.warning("no_email_for_recap", lead_id=lead.id)
        return
    
    # Build email content
    subject = f"Your Property Search Summary - {profile.city if profile else 'Dubai'}"
    
    # Property preferences section
    preferences_html = ""
    if profile:
        preferences_html = f"""
        <h2>Your Property Preferences</h2>
        <ul>
            <li><strong>Location:</strong> {profile.city or 'Dubai'}{f', {", ".join(profile.areas)}' if profile.areas else ''}</li>
            <li><strong>Property Type:</strong> {profile.property_type or 'Not specified'}</li>
            <li><strong>Bedrooms:</strong> {profile.beds or 'Not specified'}</li>
            <li><strong>Budget:</strong> {f'AED {profile.budget_min:,.0f} - {profile.budget_max:,.0f}' if profile.budget_max else 'Not specified'}</li>
            <li><strong>Timeline:</strong> {profile.move_in_date or 'Not specified'}</li>
            <li><strong>Financing:</strong> {'Pre-approved' if profile.preapproved else 'Mortgage assistance needed' if profile.financing_notes else 'Not specified'}</li>
        </ul>
        """
    
    # Top matches section
    top_matches = payload.get("top_matches", [])
    matches_html = ""
    if top_matches:
        matches_html = "<h2>Matching Properties</h2><ul>"
        for match in top_matches[:5]:  # Show top 5
            matches_html += f"""
            <li>
                <strong>{match.get('title', 'Property')}</strong><br>
                {match.get('beds', 0)} beds • {match.get('area_m2', 0)} m² • AED {match.get('price', 0):,.0f}<br>
                {match.get('location', '')}
            </li>
            """
        matches_html += "</ul>"
    
    # Next steps section
    next_steps_html = ""
    if qualification.score >= 65:
        next_steps_html = """
        <h2>Next Steps</h2>
        <p><strong>Great news!</strong> Based on your requirements, you're a priority client. 
        A senior property specialist will contact you within 24 hours to:</p>
        <ul>
            <li>Schedule property viewings</li>
            <li>Assist with mortgage pre-approval (if needed)</li>
            <li>Answer any questions you have</li>
            <li>Guide you through the buying process</li>
        </ul>
        """
    else:
        next_steps_html = f"""
        <h2>Next Steps</h2>
        <p>{qualification.suggested_next_step}</p>
        <p>We'll review your requirements and be in touch soon with more options that match your needs.</p>
        """
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            h2 {{ color: #0066cc; }}
            ul {{ padding-left: 20px; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ccc; font-size: 0.9em; color: #666; }}
        </style>
    </head>
    <body>
        <h1>Hi {contact.name or 'there'}!</h1>
        <p>Thank you for sharing your property requirements with us. Here's a summary of our conversation:</p>
        
        {preferences_html}
        {matches_html}
        {next_steps_html}
        
        <div class="footer">
            <p>If you have any questions, feel free to reply to this email or call us.</p>
            <p>Best regards,<br>Your Property Team</p>
        </div>
    </body>
    </html>
    """
    
    # For MVP: Log the email (in production, send via email service)
    logger.info(
        "email_recap_generated",
        lead_id=lead.id,
        to=contact.email,
        subject=subject,
        content_preview=html_content[:200]
    )
    
    # TODO: In production, integrate with email service:
    # import boto3  # AWS SES
    # or
    # from sendgrid import SendGridAPIClient
    # from sendgrid.helpers.mail import Mail
    # 
    # message = Mail(
    #     from_email='no-reply@yourdomain.com',
    #     to_emails=contact.email,
    #     subject=subject,
    #     html_content=html_content
    # )
    # sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    # response = sg.send(message)
    
    logger.info("email_would_be_sent_in_production", to=contact.email, subject=subject)
