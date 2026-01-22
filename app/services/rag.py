"""
RAG (Retrieval-Augmented Generation) Service
"""

import os
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
import numpy as np

from app.core.logging import get_logger
from config import settings

logger = get_logger("rag")


class RAGService:
    """Service for RAG operations using ChromaDB and sentence transformers."""

    def __init__(self):
        self.embedding_model_name = settings.EMBEDDING_MODEL
        self.persist_dir = settings.CHROMA_PERSIST_DIR
        self.embedding_model = None
        self.chroma_client = None
        self.collection = None
        self._initialized = False
        self._initialization_error = None
        # Don't initialize at import time - use lazy initialization

    def _ensure_initialized(self):
        """Lazy initialization - only initialize when first used."""
        if self._initialized:
            if self._initialization_error:
                raise RuntimeError(f"RAG service failed to initialize: {self._initialization_error}")
            return

        try:
            self._initialize()
            self._initialized = True
        except Exception as e:
            self._initialization_error = str(e)
            logger.exception("Error initializing RAG service", e)
            # Don't raise - allow app to start without RAG
            self._initialized = False

    def _initialize(self):
        """Initialize the RAG service components."""
        try:
            # Initialize embedding model
            logger.info(f"Loading embedding model: {self.embedding_model_name}")
            self.embedding_model = SentenceTransformer(self.embedding_model_name)

            # Initialize ChromaDB
            os.makedirs(self.persist_dir, exist_ok=True)
            
            # Try to fix corrupted ChromaDB database
            chroma_db_path = os.path.join(self.persist_dir, "chroma.sqlite3")
            if os.path.exists(chroma_db_path):
                try:
                    # Try to access the database
                    test_client = chromadb.PersistentClient(
                        path=self.persist_dir,
                        settings=ChromaSettings(anonymized_telemetry=False),
                    )
                    test_client.list_collections()
                except Exception as db_error:
                    logger.warning(
                        f"ChromaDB database appears corrupted, recreating",
                        context={"error": str(db_error)},
                    )
                    # Backup and remove corrupted database
                    import shutil
                    backup_path = f"{chroma_db_path}.backup"
                    if os.path.exists(chroma_db_path):
                        shutil.move(chroma_db_path, backup_path)
                    logger.info("Corrupted ChromaDB database backed up and removed")

            self.chroma_client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
            )

            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name="documents",
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("RAG service initialized successfully")
        except Exception as e:
            logger.exception("Error initializing RAG service", e)
            # Store error but don't raise - allow graceful degradation
            raise

    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings

        Returns:
            Numpy array of embeddings
        """
        self._ensure_initialized()
        if not self.embedding_model:
            raise RuntimeError("Embedding model not initialized")
        return self.embedding_model.encode(texts, show_progress_bar=False)

    def add_document(
        self, document_id: int, content: str, metadata: Optional[Dict] = None
    ):
        """
        Add a document to the vector store.

        Args:
            document_id: Database document ID
            content: Document content
            metadata: Optional metadata dictionary
        """
        try:
            self._ensure_initialized()
        except Exception as e:
            logger.error(
                f"Cannot add document {document_id}: RAG service not initialized",
                context={"error": str(e)},
            )
            raise

        if not content or not content.strip():
            logger.warning(f"Empty content for document {document_id}, skipping")
            return

        # Split content into chunks (simple approach - can be improved)
        chunk_size = 1000
        chunks = [
            content[i : i + chunk_size] for i in range(0, len(content), chunk_size)
        ]

        if not chunks:
            return

        # Generate embeddings
        embeddings = self.generate_embeddings(chunks)

        # Prepare metadata
        metadatas = []
        ids = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = {
                "document_id": str(document_id),
                "chunk_index": str(i),
                **(metadata or {}),
            }
            metadatas.append(chunk_metadata)
            ids.append(f"doc_{document_id}_chunk_{i}")

        # Add to ChromaDB
        try:
            self.collection.add(
                embeddings=embeddings.tolist(),
                documents=chunks,
                metadatas=metadatas,
                ids=ids,
            )
            logger.info(f"Added document {document_id} with {len(chunks)} chunks")
        except Exception as e:
            logger.exception(
                "Error adding document to vector store",
                e,
                context={"document_id": document_id, "chunk_count": len(chunks)},
            )
            raise

    def search(
        self, query: str, n_results: int = 5, document_ids: Optional[List[int]] = None
    ) -> List[Dict]:
        """
        Search for relevant document chunks.

        Args:
            query: Search query
            n_results: Number of results to return
            document_ids: Optional list of document IDs to filter by

        Returns:
            List of dictionaries with 'content', 'metadata', and 'distance'
        """
        try:
            self._ensure_initialized()
        except Exception as e:
            logger.error(
                f"Cannot search: RAG service not initialized",
                context={"error": str(e), "query": query},
            )
            return []

        if not query or not query.strip():
            return []

        # Generate query embedding
        query_embedding = self.generate_embeddings([query])[0]

        # Build where clause if filtering by document IDs
        where = None
        if document_ids:
            where = {"document_id": {"$in": [str(doc_id) for doc_id in document_ids]}}

        # Search in ChromaDB
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results,
                where=where,
            )

            # Format results
            formatted_results = []
            if results["documents"] and len(results["documents"]) > 0:
                for i in range(len(results["documents"][0])):
                    formatted_results.append(
                        {
                            "content": results["documents"][0][i],
                            "metadata": results["metadatas"][0][i],
                            "distance": results["distances"][0][i] if results["distances"] else None,
                        }
                    )
            return formatted_results
        except Exception as e:
            logger.exception(
                "Error searching vector store",
                e,
                context={"query": query, "n_results": n_results},
            )
            return []

    def delete_document(self, document_id: int):
        """
        Delete a document from the vector store.

        Args:
            document_id: Database document ID
        """
        try:
            self._ensure_initialized()
        except Exception as e:
            logger.warning(
                f"Cannot delete document {document_id}: RAG service not initialized",
                context={"error": str(e)},
            )
            return

        try:
            # Get all chunks for this document
            results = self.collection.get(
                where={"document_id": str(document_id)}
            )
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                logger.info(f"Deleted document {document_id} from vector store")
        except Exception as e:
            logger.exception(
                "Error deleting document from vector store",
                e,
                context={"document_id": document_id},
            )


# Singleton instance (lazy initialization - won't fail on import)
rag_service = RAGService()
