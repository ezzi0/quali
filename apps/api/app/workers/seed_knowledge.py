"""Seed FAQ and objection handling knowledge to Qdrant"""
import json
from ..deps import get_qdrant, engine
from ..services.embedding_store import QdrantEmbeddingStore
from ..logging import get_logger

logger = get_logger(__name__)


FAQ_DATA = [
    {
        "id": "qa_what_is_agency20",
        "title": "What is Agency 2.0?",
        "tags": ["qa"],
        "content": "Agency 2.0 is an AI-centered real-estate operating system. AI handles targeting, intake, profiling, affordability previews, matching, and documents. Humans focus on discovery, negotiation, and closing. The Smart Arm learns from every outcome and updates the system daily."
    },
    {
        "id": "qa_how_is_it_different",
        "title": "How is it different from a traditional agency?",
        "tags": ["qa"],
        "content": "Traditional: slow first touch, inconsistent qualification, broad ad targeting, sparse documentation. Agency 2.0: seconds-to-first-reply, consistent qualification, persona targeting, unified supply, full transcripts, and continuous learning."
    },
    {
        "id": "qa_what_data_is_used",
        "title": "What data is used?",
        "tags": ["qa"],
        "content": "Messages (WhatsApp/web/calls), form fields, campaign data, closed-won histories, developer feeds, resale portals, and KYC documents. Outcomes (wins/losses) complete the loop so the Smart Arm can update targeting, scripts, routing, and matching weights."
    },
    {
        "id": "qa_is_this_a_credit_check",
        "title": "Is this a credit check?",
        "tags": ["qa"],
        "content": "No. We run a friendly affordability preview to set expectations. It is not a credit check. We only move to formal verification if you proceed with a property and you consent."
    },
    {
        "id": "qa_will_i_speak_to_a_person",
        "title": "Will I speak to a person?",
        "tags": ["qa"],
        "content": "Yes. The AI prepares a clean profile and options; an elite closer speaks with you when you're ready so your first human call is relevant and quick."
    },
    {
        "id": "qa_data_privacy",
        "title": "How is my data protected?",
        "tags": ["qa"],
        "content": "PII is stored in a segregated vault with role-based access and full audit logs. Chat transcripts and events are logged for quality and learning. You can request deletion according to policy."
    },
    {
        "id": "qa_pilot_results_targets",
        "title": "What results should we expect?",
        "tags": ["qa"],
        "content": "Targets: time-to-first-touch ≤ 60s median; qualified lead rate ≥ 25%; show→close ≥ 2× control; rep hours per deal ↓ ≥ 30%; media CAC ↓ 30–60% or throughput ↑ ~2×, subject to supply."
    },
    {
        "id": "obj_human_better",
        "title": "Objection: A human does this today",
        "tags": ["objection"],
        "content": "Humans are best at judgment and persuasion, not repetitive intake at scale. We put humans where they are strongest and give them better-prepared buyers. The result is faster calls and higher win rates."
    },
    {
        "id": "obj_bots_cold",
        "title": "Objection: Bots feel cold",
        "tags": ["objection"],
        "content": "We ask one short question at a time, mirror the buyer's terms, and escalate to a human on any sign of frustration or VIP status. The first human call is faster and more relevant."
    },
    {
        "id": "obj_miss_whales",
        "title": "Objection: What if we miss whales?",
        "tags": ["objection"],
        "content": "We bias for upside: any VIP/HNW signal or uncertainty routes to a human immediately. We'd rather over-escalate than lose a high-value buyer."
    }
]


def seed_knowledge():
    """Seed FAQ and objection knowledge to Qdrant"""
    try:
        # Get Qdrant client and store
        qdrant_client = get_qdrant()
        embedding_store = QdrantEmbeddingStore(qdrant_client)
        
        # Create knowledge collection if it doesn't exist
        from qdrant_client.models import Distance, VectorParams
        import uuid
        
        collections = {c.name for c in qdrant_client.get_collections().collections}
        if "knowledge" not in collections:
            qdrant_client.create_collection(
                collection_name="knowledge",
                vectors_config=VectorParams(
                    size=1536,
                    distance=Distance.COSINE,
                ),
            )
            logger.info("knowledge_collection_created")
        
        # Embed each FAQ/objection
        for idx, item in enumerate(FAQ_DATA):
            # Create searchable text
            text = f"""
            {item['title']}
            
            {item['content']}
            
            Tags: {', '.join(item['tags'])}
            """.strip()
            
            # Metadata
            metadata = {
                "doc_id": item["id"],
                "title": item["title"],
                "tags": item["tags"],
                "type": item["tags"][0],  # qa or objection
                "content": item["content"],
            }
            
            # Generate UUID from string ID for consistency
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, item["id"]))
            
            # Upsert to Qdrant
            embedding_store.upsert(
                collection="knowledge",
                id=point_id,
                text=text,
                metadata=metadata,
            )
            
            logger.info("knowledge_item_embedded", id=item["id"], title=item["title"])
        
        logger.info("knowledge_seeded", count=len(FAQ_DATA))
        print(f"✅ Seeded {len(FAQ_DATA)} knowledge items to Qdrant")
    
    except Exception as e:
        logger.error("seed_knowledge_failed", error=str(e))
        raise


if __name__ == "__main__":
    seed_knowledge()

