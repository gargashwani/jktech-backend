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

    def __init__(self):
        self.embedding_model_name = settings.EMBEDDING_MODEL
        self.persist_dir = settings.CHROMA_PERSIST_DIR
        self.embedding_model = None
        self.chroma_client = None
        self.collection = None
        self._initialized = False
        self._initialization_error = None

    def _ensure_initialized(self):
        if self._initialized:
            if self._initialization_error:
                raise RuntimeError(f"RAG service failed to initialize: {self._initialization_error}")
            return

        self._initialize()
        self._initialized = True

    def _initialize(self):
        logger.info(f"Loading embedding model: {self.embedding_model_name}")
        self.embedding_model = SentenceTransformer(self.embedding_model_name)

        os.makedirs(self.persist_dir, exist_ok=True)
        
        chroma_db_path = os.path.join(self.persist_dir, "chroma.sqlite3")
        if os.path.exists(chroma_db_path):
            test_client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            test_client.list_collections()

        self.chroma_client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        self.collection = self.chroma_client.get_or_create_collection(
            name="documents",
            metadata={
                "hnsw:space": "cosine",
                "ef_construction": 200
            },
        )
        logger.info("RAG service initialized successfully")

    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        self._ensure_initialized()
        if not self.embedding_model:
            raise RuntimeError("Embedding model not initialized")
        return self.embedding_model.encode(texts, show_progress_bar=False)

    def add_document(
        self, document_id: int, content: str, metadata: Optional[Dict] = None
    ):
        self._ensure_initialized()

        if not content or not content.strip():
            logger.warning(f"Empty content for document {document_id}, skipping")
            return

        chunk_size = 1000
        chunks = [
            content[i : i + chunk_size] for i in range(0, len(content), chunk_size)
        ]

        if not chunks:
            return

        embeddings = self.generate_embeddings(chunks)

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

        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=chunks,
            metadatas=metadatas,
            ids=ids,
        )
        logger.info(f"Added document {document_id} with {len(chunks)} chunks")

    def search(
        self, query: str, n_results: int = 5, document_ids: Optional[List[int]] = None
    ) -> List[Dict]:
        self._ensure_initialized()

        if not query or not query.strip():
            return []

        query_embedding = self.generate_embeddings([query])[0]

        where = None
        if document_ids:
            where = {"document_id": {"$in": [str(doc_id) for doc_id in document_ids]}}

        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results,
            where=where,
        )

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

    def delete_document(self, document_id: int):
        self._ensure_initialized()

        results = self.collection.get(
            where={"document_id": str(document_id)}
        )
        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            logger.info(f"Deleted document {document_id} from vector store")


rag_service = RAGService()
