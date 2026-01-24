"""
Q&A API Controller for RAG System
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database_async import get_async_db
from app.core.logging import get_logger
from app.core.security_async import get_current_active_user_async
from app.models.user import User
from app.schemas.document import QARequest, QAResponse
from app.services.rag import rag_service

logger = get_logger("qa")

router = APIRouter()


@router.post("", response_model=QAResponse)
async def ask_question(
    *,
    db: AsyncSession = Depends(get_async_db),
    request: QARequest,
    current_user: User = Depends(get_current_active_user_async),
) -> Any:
    """Ask a question and get an answer using RAG."""
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question is required")

    try:
        # Search for relevant document chunks
        search_results = rag_service.search(
            query=request.question,
            n_results=5,
            document_ids=request.document_ids,
        )

        if not search_results:
            return QAResponse(
                question=request.question,
                answer="I couldn't find any relevant information in the documents to answer your question.",
                sources=[],
                confidence=0.0,
            )

        # Build context from search results
        context_parts = []
        sources = []
        for result in search_results:
            content = result["content"]
            metadata = result.get("metadata", {})
            context_parts.append(content)
            sources.append(
                {
                    "content": content[:200] + "..." if len(content) > 200 else content,
                    "document_id": int(metadata.get("document_id", 0)),
                    "chunk_index": int(metadata.get("chunk_index", 0)),
                    "filename": metadata.get("filename", "Unknown"),
                    "distance": result.get("distance"),
                }
            )

        context = "\n\n".join(context_parts)

        # Simple local answer: return the most relevant excerpts from the documents
        answer_intro = "Here are the most relevant excerpts from your documents:\n\n"
        answer = answer_intro + context

        # Calculate confidence based on search distances (lower is better)
        if search_results and search_results[0].get("distance") is not None:
            # Convert distance to confidence (inverse relationship)
            avg_distance = sum(
                r.get("distance", 1.0) for r in search_results
            ) / len(search_results)
            confidence = max(0.0, min(1.0, 1.0 - avg_distance))
        else:
            confidence = 0.5  # Default confidence

        return QAResponse(
            question=request.question,
            answer=answer,
            sources=sources,
            confidence=confidence,
        )
    except Exception as e:
        logger.exception(
            "Error processing question",
            e,
            context={
                "user_id": current_user.id,
                "question": request.question,
                "document_ids": request.document_ids,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process question",
        )
