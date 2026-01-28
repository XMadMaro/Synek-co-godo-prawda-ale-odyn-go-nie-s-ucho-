"""
Knowledge-Architect Agent - RAG Index Manager
Full implementation with chunking, embedding, and vector storage.
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime

from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.agents.base import BaseAgent
from src.core import get_settings, get_logger
from src.core.models import IndexedDocument, ScrapedContent, TextChunk
from src.infrastructure import LLMClient, QdrantService


@dataclass
class IndexRequest:
    """Input for Knowledge-Architect agent."""
    documents: list[ScrapedContent]
    collection_name: str = "knowledge_base"
    chunk_size: int = 512
    chunk_overlap: int = 50
    batch_size: int = 100  # Batch size for embedding


class KnowledgeArchitectAgent(BaseAgent[IndexRequest, list[IndexedDocument]]):
    """
    RAG knowledge base manager.

    Responsibilities:
    1. Receive scraped content from Scraper-Intel
    2. Split into optimal chunks using semantic splitting
    3. Generate embeddings via OpenAI
    4. Store in Qdrant with rich metadata
    5. Handle deduplication (by content hash)
    """

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        qdrant_service: QdrantService | None = None,
    ):
        super().__init__("knowledge_architect")
        self.settings = get_settings()
        self.llm = llm_client or LLMClient()
        self.qdrant = qdrant_service or QdrantService()

    async def execute(self, input_data: IndexRequest) -> list[IndexedDocument]:
        """
        Index all documents into vector store.
        """
        self.log.info(
            "indexing_started",
            documents_count=len(input_data.documents),
            collection=input_data.collection_name,
            chunk_size=input_data.chunk_size,
        )

        # Ensure collection exists
        await self.qdrant.ensure_collection(input_data.collection_name)

        results: list[IndexedDocument] = []
        all_chunks: list[TextChunk] = []

        # Step 1: Split all documents into chunks
        for doc in input_data.documents:
            try:
                chunks = self._split_document(
                    doc,
                    input_data.chunk_size,
                    input_data.chunk_overlap,
                )
                all_chunks.extend(chunks)

                self.log.debug(
                    "document_chunked",
                    url=doc.url,
                    chunks_count=len(chunks),
                )

            except Exception as e:
                self.log.error(
                    "chunking_failed",
                    url=doc.url,
                    error=str(e),
                )

        self.log.info("chunking_completed", total_chunks=len(all_chunks))

        # Step 2: Generate embeddings in batches
        for i in range(0, len(all_chunks), input_data.batch_size):
            batch = all_chunks[i : i + input_data.batch_size]
            batch_texts = [c.content for c in batch]

            try:
                embeddings = await self.llm.embed(batch_texts)

                # Step 3: Upsert to Qdrant
                point_ids = await self.qdrant.upsert_chunks(
                    chunks=batch,
                    embeddings=embeddings,
                    collection=input_data.collection_name,
                )

                self.log.info(
                    "batch_indexed",
                    batch_number=i // input_data.batch_size + 1,
                    chunks_count=len(batch),
                )

            except Exception as e:
                self.log.error(
                    "batch_indexing_failed",
                    batch_start=i,
                    error=str(e),
                )

        # Build result summaries per document
        doc_chunks: dict[str, list[TextChunk]] = {}
        for chunk in all_chunks:
            url = chunk.source_url
            if url not in doc_chunks:
                doc_chunks[url] = []
            doc_chunks[url].append(chunk)

        for url, chunks in doc_chunks.items():
            results.append(
                IndexedDocument(
                    document_id=hashlib.md5(url.encode()).hexdigest(),
                    chunks_count=len(chunks),
                    vector_ids=[c.id for c in chunks],
                    indexed_at=datetime.utcnow(),
                )
            )

        self.log.info(
            "indexing_completed",
            documents_indexed=len(results),
            total_chunks=len(all_chunks),
        )

        return results

    def _split_document(
        self,
        doc: ScrapedContent,
        chunk_size: int,
        chunk_overlap: int,
    ) -> list[TextChunk]:
        """
        Split document into semantic chunks.
        Uses RecursiveCharacterTextSplitter for optimal splitting.
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=[
                "\n\n",  # Paragraphs
                "\n",    # Lines
                ". ",    # Sentences
                ", ",    # Clauses
                " ",     # Words
                "",      # Characters
            ],
        )

        # Split text
        texts = splitter.split_text(doc.content)

        # Create TextChunk objects
        chunks: list[TextChunk] = []
        for idx, text in enumerate(texts):
            chunk_id = hashlib.md5(
                f"{doc.url}:{idx}:{text[:50]}".encode()
            ).hexdigest()

            chunks.append(
                TextChunk(
                    id=chunk_id,
                    content=text,
                    source_url=doc.url,
                    source_title=doc.title,
                    position=idx,
                    metadata={
                        "content_hash": doc.content_hash,
                        "scraped_at": doc.scraped_at.isoformat(),
                    },
                )
            )

        return chunks

    async def search(
        self,
        query: str,
        collection: str | None = None,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Search for relevant chunks given a query.

        Returns:
            List of relevant chunks with scores
        """
        collection = collection or "knowledge_base"

        # Generate query embedding
        query_embedding = await self.llm.embed([query])

        # Search Qdrant
        results = await self.qdrant.search(
            query_vector=query_embedding[0],
            collection=collection,
            top_k=top_k,
            min_score=self.settings.rag_min_similarity,
        )

        return [
            {
                "content": r.content,
                "source_url": r.source_url,
                "score": r.relevance_score,
            }
            for r in results
        ]

    def _build_system_prompt(self) -> str:
        return """
Jesteś Knowledge-Architect - architektem bazy wiedzy RAG.
Twoje zadanie: optymalne przetworzenie dokumentów do wektorowej bazy danych.
Priorytet: zachowanie semantycznej spójności chunków.
"""
