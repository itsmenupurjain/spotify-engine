"""
Embedder — generates vector embeddings using OpenAI text-embedding-3-small.
Embeds review bodies for semantic search and frustration phrases for clustering.
"""

import logging
from typing import List, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class Embedder:
    """Generates embeddings using OpenAI's text-embedding-3-small model."""

    def __init__(self):
        self.model = settings.embedding_model
        self.dimensions = settings.embedding_dimensions

    async def embed_texts(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Embed a list of texts. Returns list of embedding vectors (or None for failures).
        Processes in batches of 100 to respect API limits.
        """
        if not settings.openai_api_key:
            logger.error("OpenAI API key not configured for embeddings")
            return [None] * len(texts)

        try:
            import openai
            client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        except ImportError:
            logger.error("openai package not installed")
            return [None] * len(texts)

        all_embeddings = []
        batch_size = 100

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            # Clean texts (API rejects empty strings)
            cleaned = [t[:8000] if t and t.strip() else "empty" for t in batch]

            try:
                response = await client.embeddings.create(
                    model=self.model,
                    input=cleaned,
                    dimensions=self.dimensions,
                )

                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)

                logger.info(f"Embedded batch {i // batch_size + 1}: {len(batch)} texts")

            except Exception as e:
                logger.error(f"Embedding batch {i // batch_size + 1} failed: {e}")
                all_embeddings.extend([None] * len(batch))

        return all_embeddings

    async def embed_single(self, text: str) -> Optional[List[float]]:
        """Embed a single text string."""
        results = await self.embed_texts([text])
        return results[0] if results else None
