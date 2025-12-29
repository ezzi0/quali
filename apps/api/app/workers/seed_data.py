"""Seed sample data for development"""
from sqlalchemy.orm import sessionmaker

from ..deps import engine
from ..models.unit import Unit, UnitStatus
from ..models.lead import Lead, LeadProfile, LeadStatus, LeadSource
from ..models.contact import Contact
from ..models.task import Task, TaskStatus
from ..models.activity import Activity, ActivityType
from ..logging import get_logger

logger = get_logger(__name__)


def seed_units():
    """Seed sample units"""
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Check if units already exist
        from sqlalchemy import select
        existing_units = db.execute(select(Unit)).scalars().all()
        if existing_units:
            missing = [unit for unit in existing_units if not unit.image_url]
            if missing:
                logger.info("unit_images_missing", count=len(missing))
            logger.info("units_already_seeded")
            return

        sample_units = [
            {
                "title": "Marina Vista Tower",
                "slug": "marina-vista-tower",
                "developer": "Emaar Properties",
                "image_url": None,
                "price": 1200000,
                "currency": "AED",
                "price_display": "AED 1.2M",
                "payment_plan": "60/40",
                "area_m2": 120,
                "beds": 3,
                "baths": 3,
                "bedrooms_label": "Studio, 1BR, 2BR, 3BR",
                "unit_sizes": "500-2000 sqft",
                "location": "Dubai Marina",
                "city": "Dubai",
                "area": "Dubai Marina",
                "property_type": "apartment",
                "status": UnitStatus.AVAILABLE,
                "active": True,
                "featured": True,
                "handover": "Q4 2026",
                "handover_year": 2026,
                "roi": "7-9%",
                "features": ["Sea view", "Private beach", "Sky lounge", "Concierge"],
                "description": "Iconic waterfront tower with panoramic marina views and resort-style amenities.",
            },
            {
                "title": "Marina Heights",
                "slug": "marina-heights",
                "developer": "Select Group",
                "image_url": None,
                "price": 950000,
                "currency": "AED",
                "price_display": "AED 950K",
                "payment_plan": "70/30",
                "area_m2": 95,
                "beds": 2,
                "baths": 2,
                "bedrooms_label": "1BR, 2BR, 3BR",
                "unit_sizes": "620-1600 sqft",
                "location": "Dubai Marina",
                "city": "Dubai",
                "area": "Dubai Marina",
                "property_type": "apartment",
                "status": UnitStatus.AVAILABLE,
                "active": True,
                "featured": False,
                "handover": "Q2 2025",
                "handover_year": 2025,
                "roi": "8-10%",
                "features": ["Infinity pool", "Co-working lounge", "Marina walk access"],
                "description": "Modern high-rise with curated lifestyle amenities and flexible payment terms.",
            },
            {
                "title": "Marina Edge Residences",
                "slug": "marina-edge-residences",
                "developer": "Damac Properties",
                "image_url": None,
                "price": 1800000,
                "currency": "AED",
                "price_display": "AED 1.8M",
                "payment_plan": "60/40",
                "area_m2": 140,
                "beds": 3,
                "baths": 3,
                "bedrooms_label": "2BR, 3BR, 4BR",
                "unit_sizes": "950-2200 sqft",
                "location": "Dubai Marina",
                "city": "Dubai",
                "area": "Dubai Marina",
                "property_type": "apartment",
                "status": UnitStatus.AVAILABLE,
                "active": True,
                "featured": False,
                "handover": "Q1 2027",
                "handover_year": 2027,
                "roi": "6-8%",
                "features": ["Sky deck", "Kids club", "Valet", "Fitness studio"],
                "description": "Elegant residences with generous layouts and curated interiors.",
            },
            {
                "title": "Palm Crest Villas",
                "slug": "palm-crest-villas",
                "developer": "Nakheel",
                "image_url": None,
                "price": 6500000,
                "currency": "AED",
                "price_display": "AED 6.5M",
                "payment_plan": "80/20",
                "area_m2": 380,
                "beds": 5,
                "baths": 5,
                "bedrooms_label": "4BR, 5BR",
                "unit_sizes": "4,000-6,500 sqft",
                "location": "Palm Jumeirah",
                "city": "Dubai",
                "area": "Palm Jumeirah",
                "property_type": "villa",
                "status": UnitStatus.AVAILABLE,
                "active": True,
                "featured": True,
                "handover": "Q3 2025",
                "handover_year": 2025,
                "roi": "5-7%",
                "features": ["Private beach", "Garden", "Smart home", "Infinity pool"],
                "description": "Seafront villas with private beach access and bespoke interior upgrades.",
            },
            {
                "title": "Business Bay Lofts",
                "slug": "business-bay-lofts",
                "developer": "Omniyat",
                "image_url": None,
                "price": 980000,
                "currency": "AED",
                "price_display": "AED 980K",
                "payment_plan": "65/35",
                "area_m2": 88,
                "beds": 2,
                "baths": 2,
                "bedrooms_label": "Studio, 1BR, 2BR",
                "unit_sizes": "540-1,400 sqft",
                "location": "Business Bay",
                "city": "Dubai",
                "area": "Business Bay",
                "property_type": "apartment",
                "status": UnitStatus.AVAILABLE,
                "active": True,
                "featured": False,
                "handover": "Q4 2025",
                "handover_year": 2025,
                "roi": "7-9%",
                "features": ["Canal view", "Retail podium", "Co-working", "Gym"],
                "description": "Lifestyle-centric lofts in the heart of the business district.",
            },
            {
                "title": "Jumeirah Bay Estates",
                "slug": "jumeirah-bay-estates",
                "developer": "Meraas",
                "image_url": None,
                "price": 9800000,
                "currency": "AED",
                "price_display": "AED 9.8M",
                "payment_plan": "50/50",
                "area_m2": 520,
                "beds": 6,
                "baths": 7,
                "bedrooms_label": "5BR, 6BR",
                "unit_sizes": "6,500-9,000 sqft",
                "location": "Jumeirah Bay Island",
                "city": "Dubai",
                "area": "Jumeirah Bay Island",
                "property_type": "villa",
                "status": UnitStatus.AVAILABLE,
                "active": True,
                "featured": True,
                "handover": "Q2 2026",
                "handover_year": 2026,
                "roi": "6-8%",
                "features": ["Private marina", "Beach club access", "Signature spa"],
                "description": "Exclusive island villas with curated waterfront amenities.",
            },
        ]

        for unit_data in sample_units:
            unit = Unit(**unit_data)
            db.add(unit)

        db.commit()

        logger.info("units_seeded", count=len(sample_units))

    except Exception as e:
        logger.error("seed_units_failed", error=str(e))
        db.rollback()
        raise

    finally:
        db.close()


def seed_leads():
    """Seed sample leads for CRM views"""
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        from sqlalchemy import select
        existing = db.execute(select(Lead)).scalars().first()
        if existing:
            logger.info("leads_already_seeded")
            return

        sample_contacts = [
            {"name": "Noah Reed", "email": "noah.reed@example.com", "phone": "+971500000001"},
            {"name": "Aria Gomez", "email": "aria.gomez@example.com", "phone": "+971500000002"},
            {"name": "Maya Patel", "email": "maya.patel@example.com", "phone": "+971500000003"},
            {"name": "Liam Chen", "email": "liam.chen@example.com", "phone": "+971500000004"},
            {"name": "Sophia Laurent", "email": "sophia.laurent@example.com", "phone": "+971500000005"},
            {"name": "Ethan Brooks", "email": "ethan.brooks@example.com", "phone": "+971500000006"},
            {"name": "Ava Khan", "email": "ava.khan@example.com", "phone": "+971500000007"},
            {"name": "Theo Silva", "email": "theo.silva@example.com", "phone": "+971500000008"},
        ]

        created_contacts = []
        for contact_data in sample_contacts:
            contact = Contact(
                name=contact_data["name"],
                email=contact_data["email"],
                phone=contact_data["phone"],
                consent_email=True,
                consent_sms=True,
                consent_whatsapp=True,
            )
            db.add(contact)
            created_contacts.append(contact)

        db.flush()

        sample_leads = [
            {
                "status": LeadStatus.NEW,
                "assigned_to": None,
                "notes": "Needs intro to Dubai Marina options.",
                "profile": {
                    "city": "Dubai",
                    "areas": ["Dubai Marina"],
                    "property_type": "apartment",
                    "beds": 2,
                    "budget_min": 900000,
                    "budget_max": 1400000,
                    "move_in_date": "2026",
                },
            },
            {
                "status": LeadStatus.CONTACTED,
                "assigned_to": "Eli",
                "notes": "Asked about flexible payment plans.",
                "profile": {
                    "city": "Dubai",
                    "areas": ["Business Bay"],
                    "property_type": "apartment",
                    "beds": 1,
                    "budget_min": 700000,
                    "budget_max": 1100000,
                    "move_in_date": "2025",
                },
            },
            {
                "status": LeadStatus.QUALIFIED,
                "assigned_to": "Eli",
                "notes": "Investor prefers waterfront.",
                "profile": {
                    "city": "Dubai",
                    "areas": ["Palm Jumeirah", "Dubai Marina"],
                    "property_type": "villa",
                    "beds": 4,
                    "budget_min": 4500000,
                    "budget_max": 7000000,
                    "move_in_date": "2026",
                },
            },
            {
                "status": LeadStatus.VIEWING,
                "assigned_to": "Maya",
                "notes": "Scheduling virtual tour.",
                "profile": {
                    "city": "Dubai",
                    "areas": ["Downtown Dubai"],
                    "property_type": "apartment",
                    "beds": 3,
                    "budget_min": 1800000,
                    "budget_max": 2600000,
                    "move_in_date": "2027",
                },
            },
            {
                "status": LeadStatus.OFFER,
                "assigned_to": "Maya",
                "notes": "Offer draft sent.",
                "profile": {
                    "city": "Dubai",
                    "areas": ["Dubai Hills"],
                    "property_type": "townhouse",
                    "beds": 3,
                    "budget_min": 2300000,
                    "budget_max": 3200000,
                    "move_in_date": "2026",
                },
            },
            {
                "status": LeadStatus.NURTURE,
                "assigned_to": "Eli",
                "notes": "Waiting on updated inventory.",
                "profile": {
                    "city": "Dubai",
                    "areas": ["Jumeirah Village Circle"],
                    "property_type": "apartment",
                    "beds": 2,
                    "budget_min": 850000,
                    "budget_max": 1200000,
                    "move_in_date": "2028",
                },
            },
            {
                "status": LeadStatus.WON,
                "assigned_to": "Eli",
                "notes": "Closed - contract signed.",
                "profile": {
                    "city": "Dubai",
                    "areas": ["Business Bay"],
                    "property_type": "apartment",
                    "beds": 1,
                    "budget_min": 1100000,
                    "budget_max": 1300000,
                    "move_in_date": "2025",
                },
            },
            {
                "status": LeadStatus.LOST,
                "assigned_to": "Maya",
                "notes": "Paused for Q4.",
                "profile": {
                    "city": "Dubai",
                    "areas": ["Dubai Creek Harbour"],
                    "property_type": "apartment",
                    "beds": 2,
                    "budget_min": 1200000,
                    "budget_max": 1600000,
                    "move_in_date": "2027",
                },
            },
        ]

        for idx, lead_data in enumerate(sample_leads):
            contact = created_contacts[idx]
            lead = Lead(
                source=LeadSource.WEB,
                status=lead_data["status"],
                contact_id=contact.id,
                notes=lead_data["notes"],
                assigned_to=lead_data["assigned_to"],
            )
            db.add(lead)
            db.flush()

            profile_data = lead_data["profile"]
            profile = LeadProfile(
                lead_id=lead.id,
                city=profile_data["city"],
                areas=profile_data["areas"],
                property_type=profile_data["property_type"],
                beds=profile_data["beds"],
                budget_min=profile_data["budget_min"],
                budget_max=profile_data["budget_max"],
                move_in_date=profile_data["move_in_date"],
            )
            db.add(profile)

            activity = Activity(
                lead_id=lead.id,
                type=ActivityType.MESSAGE,
                payload={"note": lead_data["notes"]},
            )
            db.add(activity)

            task = Task(
                lead_id=lead.id,
                title="Follow up",
                description="Check in with lead and confirm next steps.",
                status=TaskStatus.TODO,
                assignee=lead_data["assigned_to"],
            )
            db.add(task)

        db.commit()
        logger.info("leads_seeded", count=len(sample_leads))

    except Exception as e:
        logger.error("seed_leads_failed", error=str(e))
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    from ..models.base import Base
    Base.metadata.create_all(bind=engine)
    seed_units()
    seed_leads()
