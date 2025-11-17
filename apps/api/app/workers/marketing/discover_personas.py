"""
Persona Discovery Worker

Runs daily to discover new marketing personas from recent lead data.
"""
from sqlalchemy.orm import Session
from ...deps import get_db
from ...services.marketing.persona_discovery import PersonaDiscoveryService
from ...logging import get_logger

logger = get_logger(__name__)


def discover_personas_job():
    """
    Daily job to discover marketing personas.
    
    Schedule: Daily at 7:00 AM
    Duration: ~5-10 minutes depending on data volume
    """
    logger.info("persona_discovery_job_started")
    
    db: Session = next(get_db())
    
    try:
        service = PersonaDiscoveryService(db)
        personas = service.discover_personas(
            min_cluster_size=25,
            min_samples=5,
            method="hdbscan"
        )
        
        logger.info("persona_discovery_job_completed", 
                   personas_discovered=len(personas))
        
        return {
            "status": "success",
            "personas_discovered": len(personas),
            "persona_ids": [p.id for p in personas]
        }
        
    except Exception as e:
        logger.error("persona_discovery_job_failed", error=str(e))
        raise
    
    finally:
        db.close()


if __name__ == "__main__":
    # For manual execution
    discover_personas_job()

