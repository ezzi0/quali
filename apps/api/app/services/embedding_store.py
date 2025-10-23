"""Vector embedding store abstraction and Qdrant implementation"""
from typing import Protocol, List, Dict, Any, Optional
from dataclasses import dataclass
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
import openai
from openai import OpenAI

from ..config import get_settings

settings = get_settings()


@dataclass
class SearchResult:
    """Search result from vector store"""
    id: str
    score: float
    metadata: Dict[str, Any]


class EmbeddingStore(Protocol):
    """Abstract interface for vector embedding storage"""

    def upsert(self, collection: str, id: str, text: str, metadata: Dict[str, Any]) -> None:
        """Upsert a document with its embedding"""
        ...

    def query(
        self,
        collection: str,
        query_text: str,
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Search for similar documents"""
        ...

    def delete(self, collection: str, id: str) -> None:
        """Delete a document"""
        ...


class QdrantEmbeddingStore:
    """Qdrant implementation of embedding store"""

    EMBEDDING_DIM = 1536  # OpenAI text-embedding-3-small

    def __init__(self, client: QdrantClient):
        self.client = client
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        self._ensure_collections()

    def _ensure_collections(self):
        """Create collections if they don't exist"""
        collections = ["units", "lead_memories"]

        existing = {c.name for c in self.client.get_collections().collections}

        for collection in collections:
            if collection not in existing:
                self.client.create_collection(
                    collection_name=collection,
                    vectors_config=VectorParams(
                        size=self.EMBEDDING_DIM,
                        distance=Distance.COSINE,
                    ),
                )

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding from OpenAI"""
        response = self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding

    def upsert(self, collection: str, id: str, text: str, metadata: Dict[str, Any]) -> None:
        """Upsert a document with its embedding"""
        embedding = self._get_embedding(text)

        point = PointStruct(
            id=id,
            vector=embedding,
            payload={"text": text, **metadata},
        )

        self.client.upsert(
            collection_name=collection,
            points=[point],
        )

    def query(
        self,
        collection: str,
        query_text: str,
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Search for similar documents"""
        query_embedding = self._get_embedding(query_text)

        # Build filter if provided
        qdrant_filter = None
        if filter:
            conditions = []
            for key, value in filter.items():
                conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=value))
                )
            if conditions:
                qdrant_filter = Filter(must=conditions)

        results = self.client.search(
            collection_name=collection,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=qdrant_filter,
        )

        return [
            SearchResult(
                id=str(result.id),
                score=result.score,
                metadata=result.payload or {},
            )
            for result in results
        ]

    def delete(self, collection: str, id: str) -> None:
        """Delete a document"""
        self.client.delete(
            collection_name=collection,
            points_selector=[id],
        )
