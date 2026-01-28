"""
Qdrant Client - Vector database operations.
"""

from typing import Any
from uuid import uuid4

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
    Filter,
    FieldCondition,
    MatchValue,
)

from src.core import get_settings, get_logger
from src.core.models import TextChunk, Evidence


class QdrantService:
    """
    Qdrant vector database service.

    Handles:
    - Collection management
    - Document indexing (upsert)
    - Similarity search
    - Filtering by metadata
    """

    def __init__(self):
        settings = get_settings()
        self.client = AsyncQdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
        )
        self.log = get_logger("qdrant")
        self.default_collection = "knowledge_base"

    async def ensure_collection(
        self,
        name: str,
        vector_size: int = 1536,  # OpenAI text-embedding-3-small
    ) -> bool:
        """Create collection if it doesn't exist."""
        try:
            collections = await self.client.get_collections()
            existing = [c.name for c in collections.collections]

            if name not in existing:
                await self.client.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE,
                    ),
                )
                self.log.info("collection_created", name=name, vector_size=vector_size)
                return True

            return False

        except Exception as e:
            self.log.error("collection_error", name=name, error=str(e))
            raise

    async def upsert_chunks(
        self,
        chunks: list[TextChunk],
        embeddings: list[list[float]],
        collection: str | None = None,
    ) -> list[str]:
        """
        Insert or update chunks with embeddings.

        Returns:
            List of point IDs
        """
        collection = collection or self.default_collection
        await self.ensure_collection(collection)

        points = []
        point_ids = []

        for chunk, embedding in zip(chunks, embeddings):
            point_id = chunk.id or str(uuid4())
            point_ids.append(point_id)

            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "content": chunk.content,
                        "source_url": chunk.source_url,
                        "source_title": chunk.source_title,
                        "position": chunk.position,
                        **chunk.metadata,
                    },
                )
            )

        try:
            await self.client.upsert(
                collection_name=collection,
                points=points,
            )

            self.log.info(
                "chunks_upserted",
                collection=collection,
                count=len(points),
            )

            return point_ids

        except Exception as e:
            self.log.error("upsert_error", collection=collection, error=str(e))
            raise

    async def search(
        self,
        query_vector: list[float],
        collection: str | None = None,
        top_k: int = 5,
        min_score: float = 0.7,
        filter_url: str | None = None,
    ) -> list[Evidence]:
        """
        Search for similar documents.

        Returns:
            List of Evidence objects with relevance scores
        """
        collection = collection or self.default_collection

        # Build filter if URL specified
        query_filter = None
        if filter_url:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="source_url",
                        match=MatchValue(value=filter_url),
                    )
                ]
            )

        try:
            results = await self.client.search(
                collection_name=collection,
                query_vector=query_vector,
                limit=top_k,
                score_threshold=min_score,
                query_filter=query_filter,
            )

            evidence_list = []
            for result in results:
                evidence_list.append(
                    Evidence(
                        source_url=result.payload.get("source_url", ""),
                        content=result.payload.get("content", ""),
                        relevance_score=result.score,
                    )
                )

            self.log.debug(
                "search_completed",
                collection=collection,
                results_count=len(evidence_list),
            )

            return evidence_list

        except Exception as e:
            self.log.error("search_error", collection=collection, error=str(e))
            raise

    async def delete_by_url(self, url: str, collection: str | None = None) -> int:
        """Delete all chunks from a specific URL."""
        collection = collection or self.default_collection

        try:
            result = await self.client.delete(
                collection_name=collection,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="source_url",
                            match=MatchValue(value=url),
                        )
                    ]
                ),
            )

            self.log.info("chunks_deleted", collection=collection, url=url)
            return 1  # Qdrant doesn't return count

        except Exception as e:
            self.log.error("delete_error", collection=collection, url=url, error=str(e))
            raise

    async def get_collection_stats(self, collection: str | None = None) -> dict:
        """Get collection statistics."""
        collection = collection or self.default_collection

        try:
            info = await self.client.get_collection(collection)
            return {
                "name": collection,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status.name,
            }
        except Exception as e:
            self.log.error("stats_error", collection=collection, error=str(e))
            return {"name": collection, "error": str(e)}
