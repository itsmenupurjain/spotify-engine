"""
Play Store scraper — fetches Spotify reviews from the Google Play Store.
Uses the google-play-scraper Python package.
"""

import logging
import asyncio
from typing import List, Dict, Any

from app.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

SPOTIFY_PACKAGE = "com.spotify.music"


class PlayStoreScraper(BaseScraper):
    """Scraper for Google Play Store Spotify reviews."""

    SOURCE_NAME = "play_store"

    def __init__(self, count: int = 1000):
        super().__init__()
        self.count = count

    async def scrape(self) -> List[Dict[str, Any]]:
        """Fetch Spotify Play Store reviews sorted by relevance and recency."""
        try:
            from google_play_scraper import Sort, reviews as gp_reviews
        except ImportError:
            logger.error("google-play-scraper not installed. Run: pip install google-play-scraper")
            return []

        all_reviews = []

        # Fetch by both relevance and newest
        for sort_order, sort_name in [(Sort.MOST_RELEVANT, "relevance"), (Sort.NEWEST, "newest")]:
            try:
                batch_count = self.count // 2

                result, _ = await self._retry_with_backoff(
                    self._fetch_reviews, gp_reviews, sort_order, batch_count
                )

                for review in result:
                    parsed = self._parse_review(review)
                    if parsed:
                        all_reviews.append(parsed)

                logger.info(f"[play_store] Fetched {len(result)} reviews sorted by {sort_name}")

            except Exception as e:
                logger.error(f"[play_store] Error fetching by {sort_name}: {e}")
                self.stats["entries_failed"] += 1

        return all_reviews

    async def _fetch_reviews(self, gp_reviews_func, sort_order, count):
        """Fetch reviews (runs in executor for sync library)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: gp_reviews_func(
                SPOTIFY_PACKAGE,
                lang="en",
                country="us",
                sort=sort_order,
                count=count,
            ),
        )

    def _parse_review(self, review: dict) -> Dict[str, Any]:
        """Parse a single Play Store review into our RawReview schema."""
        try:
            return {
                "source": "play_store",
                "external_id": f"play_store_{review.get('reviewId', '')}",
                "rating": review.get("score"),
                "title": None,  # Play Store reviews often have no title
                "body": review.get("content", ""),
                "author_hash": self._hash_author(review.get("userName", "anonymous")),
                "published_at": review.get("at"),
                "app_version": review.get("reviewCreatedVersion"),
                "country_code": "US",
                "engagement_score": review.get("thumbsUpCount", 0),
                "raw_url": f"https://play.google.com/store/apps/details?id={SPOTIFY_PACKAGE}",
                "language": None,
            }
        except Exception as e:
            logger.error(f"[play_store] Failed to parse review: {e}")
            return None
