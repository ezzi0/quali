"""
RAG (Retrieval Augmented Generation) for Knowledge Base

Enables the agent to search FAQs and objection handling from Qdrant.
"""
from typing import List, Dict, Any
from ..deps import get_qdrant
from ..services.embedding_store import QdrantEmbeddingStore
from ..logging import get_logger

logger = get_logger(__name__)


def knowledge_search(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Search the knowledge base for relevant FAQs and objection handlers.
    
    Uses RAG (Retrieval Augmented Generation):
    1. Embed the query
    2. Search Qdrant for similar documents
    3. Return top matching FAQs/objections
    
    Args:
        query: User's question or objection
        top_k: Number of results to return (default: 3)
    
    Returns:
        List of matching knowledge items with title and content
    """
    try:
        qdrant_client = get_qdrant()
        embedding_store = QdrantEmbeddingStore(qdrant_client)
        
        # Search knowledge collection
        results = embedding_store.query(
            collection="knowledge",
            query_text=query,
            top_k=top_k
        )
        
        # Format results
        knowledge_items = []
        for result in results:
            knowledge_items.append({
                "title": result.metadata.get("title", ""),
                "content": result.metadata.get("content", ""),
                "type": result.metadata.get("type", ""),
                "relevance_score": round(result.score, 3),
            })
        
        logger.info("knowledge_search", query=query, results_count=len(knowledge_items))
        
        return knowledge_items
    
    except Exception as e:
        logger.error("knowledge_search_failed", query=query, error=str(e))
        return []

