"""
OpenRouter Service for Llama3 Integration
"""

import httpx
from typing import Optional

from app.core.logging import get_logger
from config import settings

logger = get_logger("openrouter")


class OpenRouterService:
    """Service for interacting with OpenRouter API (Llama3)."""

    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL
        self.model = settings.OPENROUTER_MODEL

    async def generate_summary(self, content: str, context: Optional[str] = None) -> str:
        """
        Generate a summary using Llama3 via OpenRouter.

        Args:
            content: The content to summarize
            context: Optional context to provide to the model

        Returns:
            Generated summary text
        """
        if not self.api_key:
            logger.warning(
                "OpenRouter API key not set, returning placeholder summary",
                context={"content_length": len(content)},
            )
            return f"Summary for: {content[:100]}..."

        prompt = f"""Please provide a concise summary of the following content.
        
Content:
{content}
"""

        if context:
            prompt = f"""Context: {context}

Please provide a concise summary of the following content based on the context above.

Content:
{content}
"""

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a helpful assistant that provides concise and accurate summaries.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.7,
                        "max_tokens": 500,
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.exception(
                "Error generating summary with OpenRouter",
                e,
                context={"content_length": len(content)},
            )
            # Fallback to a simple summary
            return f"Summary: {content[:200]}..." if len(content) > 200 else content

    async def generate_review_summary(self, reviews: list[dict]) -> str:
        """
        Generate a summary of book reviews.

        Args:
            reviews: List of review dictionaries with 'rating' and 'review_text'

        Returns:
            Generated review summary
        """
        if not reviews:
            return "No reviews available."

        if not self.api_key:
            avg_rating = sum(r.get("rating", 0) for r in reviews) / len(reviews)
            return f"Average rating: {avg_rating:.1f}/5 based on {len(reviews)} reviews."

        reviews_text = "\n\n".join(
            [
                f"Rating: {r.get('rating', 'N/A')}/5\nReview: {r.get('review_text', '')}"
                for r in reviews
            ]
        )

        prompt = f"""Please provide a concise summary of the following book reviews, highlighting common themes, overall sentiment, and key points mentioned by reviewers.

Reviews:
{reviews_text}

Provide a summary that captures the overall sentiment and main points from these reviews."""

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a helpful assistant that summarizes book reviews.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.7,
                        "max_tokens": 500,
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.exception(
                "Error generating review summary with OpenRouter",
                e,
                context={"review_count": len(reviews)},
            )
            avg_rating = sum(r.get("rating", 0) for r in reviews) / len(reviews)
            return f"Average rating: {avg_rating:.1f}/5 based on {len(reviews)} reviews."

    async def answer_question(self, question: str, context: str) -> str:
        """
        Answer a question based on provided context using RAG.

        Args:
            question: The question to answer
            context: Relevant context/document excerpts

        Returns:
            Answer to the question
        """
        if not self.api_key:
            return "I need an API key to answer questions. Please configure OpenRouter API key."

        prompt = f"""Based on the following context, please answer the question. If the answer cannot be found in the context, say so.

Context:
{context}

Question: {question}

Answer:"""

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a helpful assistant that answers questions based on provided context. If the answer is not in the context, say so.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.7,
                        "max_tokens": 1000,
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error(
                    "OpenRouter API authentication failed. Please check your OPENROUTER_API_KEY in .env file.",
                    context={"question_length": len(question), "context_length": len(context)},
                )
                return "I'm sorry, I couldn't answer your question because the AI service is not properly configured. Please contact the administrator."
            else:
                logger.exception(
                    "Error answering question with OpenRouter",
                    e,
                    context={"question_length": len(question), "context_length": len(context), "status_code": e.response.status_code},
                )
                return "I'm sorry, I encountered an error while trying to answer your question. Please try again later."
        except Exception as e:
            logger.exception(
                "Error answering question with OpenRouter",
                e,
                context={"question_length": len(question), "context_length": len(context)},
            )
            return "I'm sorry, I encountered an error while trying to answer your question. Please try again later."


# Singleton instance
openrouter_service = OpenRouterService()
