"""Seed sample data for development"""
from sqlalchemy.orm import sessionmaker

from ..deps import engine
from ..models.unit import Unit, UnitStatus
from ..logging import get_logger

logger = get_logger(__name__)


def seed_units():
    """Seed sample units"""
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Check if units already exist
        from sqlalchemy import select
        existing = db.execute(select(Unit)).scalars().first()
        if existing:
            logger.info("units_already_seeded")
            return

        sample_units = [
            {
                "title": "Spacious 2BR Apartment in Dubai Marina",
                "price": 150000,
                "currency": "AED",
                "area_m2": 120,
                "beds": 2,
                "baths": 2,
                "location": "Dubai Marina, Dubai",
                "city": "Dubai",
                "area": "Dubai Marina",
                "property_type": "apartment",
                "status": UnitStatus.AVAILABLE,
                "features": ["pool", "gym", "parking", "sea_view"],
                "description": "Beautiful 2-bedroom apartment with stunning marina views. Fully furnished with modern amenities.",
            },
            {
                "title": "Luxury 3BR Villa in Arabian Ranches",
                "price": 3500000,
                "currency": "AED",
                "area_m2": 280,
                "beds": 3,
                "baths": 4,
                "location": "Arabian Ranches, Dubai",
                "city": "Dubai",
                "area": "Arabian Ranches",
                "property_type": "villa",
                "status": UnitStatus.AVAILABLE,
                "features": ["pool", "garden", "maid_room", "garage"],
                "description": "Stunning 3-bedroom villa in a gated community. Perfect for families.",
            },
            {
                "title": "Modern 1BR Studio in Downtown Dubai",
                "price": 95000,
                "currency": "AED",
                "area_m2": 65,
                "beds": 1,
                "baths": 1,
                "location": "Downtown Dubai, Dubai",
                "city": "Dubai",
                "area": "Downtown",
                "property_type": "apartment",
                "status": UnitStatus.AVAILABLE,
                "features": ["gym", "pool", "concierge"],
                "description": "Compact studio perfect for professionals. Walking distance to Burj Khalifa.",
            },
            {
                "title": "Elegant 2BR Townhouse in Jumeirah Village",
                "price": 1800000,
                "currency": "AED",
                "area_m2": 180,
                "beds": 2,
                "baths": 3,
                "location": "Jumeirah Village, Dubai",
                "city": "Dubai",
                "area": "Jumeirah Village",
                "property_type": "townhouse",
                "status": UnitStatus.AVAILABLE,
                "features": ["parking", "garden", "community_pool"],
                "description": "Spacious townhouse with modern design. Great for small families.",
            },
            {
                "title": "Penthouse 4BR Apartment in Palm Jumeirah",
                "price": 8500000,
                "currency": "AED",
                "area_m2": 450,
                "beds": 4,
                "baths": 5,
                "location": "Palm Jumeirah, Dubai",
                "city": "Dubai",
                "area": "Palm Jumeirah",
                "property_type": "apartment",
                "status": UnitStatus.AVAILABLE,
                "features": ["beach_access", "private_pool", "gym", "spa", "parking"],
                "description": "Ultra-luxury penthouse with panoramic sea views. Private elevator and beach access.",
            },
            {
                "title": "Affordable 1BR in International City",
                "price": 45000,
                "currency": "AED",
                "area_m2": 55,
                "beds": 1,
                "baths": 1,
                "location": "International City, Dubai",
                "city": "Dubai",
                "area": "International City",
                "property_type": "apartment",
                "status": UnitStatus.AVAILABLE,
                "features": ["parking", "gym"],
                "description": "Budget-friendly apartment perfect for first-time renters.",
            },
            {
                "title": "Family 3BR Apartment in Business Bay",
                "price": 180000,
                "currency": "AED",
                "area_m2": 160,
                "beds": 3,
                "baths": 3,
                "location": "Business Bay, Dubai",
                "city": "Dubai",
                "area": "Business Bay",
                "property_type": "apartment",
                "status": UnitStatus.AVAILABLE,
                "features": ["balcony", "parking", "gym", "pool"],
                "description": "Spacious family apartment with canal views. Close to schools and metro.",
            },
            {
                "title": "Cozy 2BR in JBR",
                "price": 165000,
                "currency": "AED",
                "area_m2": 130,
                "beds": 2,
                "baths": 2,
                "location": "Jumeirah Beach Residence, Dubai",
                "city": "Dubai",
                "area": "JBR",
                "property_type": "apartment",
                "status": UnitStatus.AVAILABLE,
                "features": ["beach_access", "pool", "gym", "parking"],
                "description": "Beachfront apartment with direct access to The Walk. Vibrant community.",
            },
            # Luxury Palm Jumeirah Villas
            {
                "title": "Signature 6BR Villa on Palm Jumeirah Frond",
                "price": 45000000,
                "currency": "AED",
                "area_m2": 850,
                "beds": 6,
                "baths": 7,
                "location": "Palm Jumeirah, Dubai",
                "city": "Dubai",
                "area": "Palm Jumeirah",
                "property_type": "villa",
                "status": UnitStatus.AVAILABLE,
                "features": ["private_beach", "pool", "maid_room", "garage", "elevator", "cinema", "gym"],
                "description": "Stunning 6-bedroom signature villa with direct beach access, private pool, and marina skyline views. Fully upgraded with smart home features.",
            },
            {
                "title": "Grand 8BR Garden Home - Palm Jumeirah",
                "price": 65000000,
                "currency": "AED",
                "area_m2": 1200,
                "beds": 8,
                "baths": 9,
                "location": "Palm Jumeirah, Dubai",
                "city": "Dubai",
                "area": "Palm Jumeirah",
                "property_type": "villa",
                "status": UnitStatus.AVAILABLE,
                "features": ["private_beach", "pool", "jacuzzi", "3_maid_rooms", "garage", "elevator", "study", "basement"],
                "description": "Exceptional 8-bedroom garden home on prime frond location. Breathtaking Atlantis and skyline views, extensive outdoor space with infinity pool.",
            },
            {
                "title": "Ultra-Luxury 10BR Signature Villa - Palm Jumeirah",
                "price": 95000000,
                "currency": "AED",
                "area_m2": 1800,
                "beds": 10,
                "baths": 12,
                "location": "Palm Jumeirah, Dubai",
                "city": "Dubai",
                "area": "Palm Jumeirah",
                "property_type": "villa",
                "status": UnitStatus.AVAILABLE,
                "features": ["private_beach", "infinity_pool", "spa", "cinema", "gym", "5_maid_rooms", "garage", "elevator", "wine_cellar", "beach_deck"],
                "description": "Palatial 10-bedroom signature villa on Palm Jumeirah tip. Bespoke finishes, 180-degree ocean views, private beach deck, and dock access. The ultimate in luxury living.",
            },
            {
                "title": "Contemporary 7BR Villa - Emirates Hills",
                "price": 55000000,
                "currency": "AED",
                "area_m2": 1100,
                "beds": 7,
                "baths": 8,
                "location": "Emirates Hills, Dubai",
                "city": "Dubai",
                "area": "Emirates Hills",
                "property_type": "villa",
                "status": UnitStatus.AVAILABLE,
                "features": ["golf_view", "pool", "maid_room", "garage", "gym", "cinema"],
                "description": "Magnificent 7-bedroom villa overlooking Emirates Golf Course. Modern architecture with premium finishes throughout.",
            },
            {
                "title": "Waterfront 6BR Villa - Dubai Hills Estate",
                "price": 38000000,
                "currency": "AED",
                "area_m2": 900,
                "beds": 6,
                "baths": 7,
                "location": "Dubai Hills Estate, Dubai",
                "city": "Dubai",
                "area": "Dubai Hills Estate",
                "property_type": "villa",
                "status": UnitStatus.AVAILABLE,
                "features": ["lake_view", "pool", "maid_room", "garage", "garden"],
                "description": "Stunning 6-bedroom villa with lake and golf course views. Contemporary design in prestigious community.",
            },
            {
                "title": "Exclusive 5BR Villa - Jumeirah Bay Island",
                "price": 48000000,
                "currency": "AED",
                "area_m2": 750,
                "beds": 5,
                "baths": 6,
                "location": "Jumeirah Bay Island, Dubai",
                "city": "Dubai",
                "area": "Jumeirah Bay Island",
                "property_type": "villa",
                "status": UnitStatus.AVAILABLE,
                "features": ["beach_access", "pool", "maid_room", "garage", "smart_home"],
                "description": "Exceptional 5-bedroom villa on exclusive Jumeirah Bay Island. Ultra-luxury finishes with private beach access.",
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


if __name__ == "__main__":
    from ..models.base import Base
    Base.metadata.create_all(bind=engine)
    seed_units()
