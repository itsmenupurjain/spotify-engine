"""
Base scraper — abstract class providing retry logic, rate limiting, and metrics tracking.
All source-specific scrapers inherit from this.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for all source scrapers."""

    SOURCE_NAME: str = "unknown"

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay  # seconds for exponential backoff
        self.stats = {
            "started_at": None,
            "completed_at": None,
            "entries_fetched": 0,
            "entries_failed": 0,
            "retries": 0,
        }

    async def run(self) -> List[Dict[str, Any]]:
        """
        Execute the scraper with retry logic and stats tracking.
        Returns a list of raw review dicts ready for database insertion.
        """
        self.stats["started_at"] = datetime.now(timezone.utc)
        logger.info(f"[{self.SOURCE_NAME}] Starting scrape...")

        try:
            results = await self.scrape()
            self.stats["entries_fetched"] = len(results)
            logger.info(f"[{self.SOURCE_NAME}] Scraped {len(results)} entries")
            return results
        except Exception as e:
            logger.error(f"[{self.SOURCE_NAME}] Scrape failed: {e}")
            self.stats["entries_failed"] += 1
            raise
        finally:
            self.stats["completed_at"] = datetime.now(timezone.utc)

    @abstractmethod
    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Implement source-specific scraping logic.
        Must return a list of dicts matching RawReview schema fields.
        """
        pass

    async def _retry_with_backoff(self, func, *args, **kwargs):
        """Execute a function with exponential backoff retry."""
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                self.stats["retries"] += 1
                delay = self.base_delay * (2 ** attempt)

                if attempt < self.max_retries - 1:
                    logger.warning(
                        f"[{self.SOURCE_NAME}] Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"[{self.SOURCE_NAME}] All {self.max_retries} attempts failed."
                    )

        raise last_exception

    def _hash_author(self, username: str) -> str:
        """Hash author username for privacy compliance."""
        import hashlib
        return hashlib.sha256(username.encode("utf-8")).hexdigest()[:16]

    def get_stats(self) -> Dict[str, Any]:
        """Return scraping run statistics."""
        return {
            "source": self.SOURCE_NAME,
            **self.stats,
        }
