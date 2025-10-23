"""Worker to embed units into Qdrant"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..deps import get_db, get_qdrant, engine
from ..models.unit import Unit, UnitStatus
from ..services.embedding_store import QdrantEmbeddingStore
from ..logging import get_logger

logger = get_logger(__name__)


def embed_all_units():
    """Embed all available units to Qdrant"""
    # Create session
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Get Qdrant client and store
        qdrant_client = get_qdrant()
        embedding_store = QdrantEmbeddingStore(qdrant_client)

        # Get all available units
        units = db.execute(
            select(Unit).where(Unit.status == UnitStatus.AVAILABLE)
        ).scalars().all()

        logger.info("embedding_units_started", count=len(units))

        for unit in units:
            # Create text representation
            text = f"""
            {unit.title}
            Type: {unit.property_type}
            Location: {unit.location}, {unit.city}, {unit.area}
            Bedrooms: {unit.beds}
            Area: {unit.area_m2} sqm
            Price: {unit.price} {unit.currency}
            Features: {', '.join(unit.features or [])}
            Description: {unit.description or ''}
            """.strip()

            # Metadata
            metadata = {
                "unit_id": unit.id,
                "title": unit.title,
                "price": float(unit.price),
                "currency": unit.currency,
                "beds": unit.beds,
                "area_m2": unit.area_m2,
                "location": unit.location,
                "city": unit.city or "",
                "area": unit.area or "",
                "property_type": unit.property_type,
            }

            # Upsert to Qdrant
            embedding_store.upsert(
                collection="units",
                id=str(unit.id),
                text=text,
                metadata=metadata,
            )

            logger.info("unit_embedded", unit_id=unit.id)

        logger.info("embedding_units_completed", count=len(units))

    except Exception as e:
        logger.error("embedding_units_failed", error=str(e))
        raise

    finally:
        db.close()


if __name__ == "__main__":
    embed_all_units()
