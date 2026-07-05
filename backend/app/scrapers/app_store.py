"""
App Store scraper — fetches Spotify reviews from the Apple App Store.
Uses the app-store-scraper Python package.
"""

import logging
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any

from app.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

SPOTIFY_APP_ID = 324684580


class AppStoreScraper(BaseScraper):
    """Scraper for Apple App Store Spotify reviews."""

    SOURCE_NAME = "app_store"

    def __init__(self, count: int = 1000, countries: List[str] = None):
        super().__init__()
        self.count = count
        self.countries = countries or ["us", "gb", "ca", "au"]

    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Fetch Spotify App Store reviews using app-store-scraper.
        Prioritizes 1-3 star reviews for highest frustration signal.
        """
        try:
            from app_store_scraper import AppStore
        except ImportError:
            logger.error("app-store-scraper not installed. Run: pip install app-store-scraper")
            return []

        all_reviews = []

        for country in self.countries:
            try:
                app = AppStore(country=country, app_name="spotify-music", app_id=SPOTIFY_APP_ID)

                reviews_per_country = self.count // len(self.countries)

                # Fetch reviews
                await self._retry_with_backoff(
                    self._fetch_reviews, app, reviews_per_country
                )

                for review in app.reviews:
                    parsed = self._parse_review(review, country)
                    if parsed:
                        all_reviews.append(parsed)

                logger.info(f"[app_store] Fetched {len(app.reviews)} reviews from {country.upper()}")

            except Exception as e:
                logger.error(f"[app_store] Error fetching from {country}: {e}")
                self.stats["entries_failed"] += 1

        return all_reviews

    async def _fetch_reviews(self, app, count: int):
        """Fetch reviews from the App Store (runs in executor for sync library)."""
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: app.review(how_many=count))

    def _parse_review(self, review: dict, country: str) -> Dict[str, Any]:
        """Parse a single App Store review into our RawReview schema."""
        try:
            return {
                "source": "app_store",
                "external_id": f"app_store_{review.get('userName', '')}_{review.get('date', '')}",
                "rating": review.get("rating"),
                "title": review.get("title"),
                "body": review.get("review", ""),
                "author_hash": self._hash_author(review.get("userName", "anonymous")),
                "published_at": review.get("date"),
                "app_version": review.get("version"),
                "country_code": country.upper(),
                "engagement_score": review.get("thumbsUp", 0),
                "raw_url": f"https://apps.apple.com/{country}/app/spotify-music/id{SPOTIFY_APP_ID}",
                "language": None,  # Set during pipeline cleaning
            }
        except Exception as e:
            logger.error(f"[app_store] Failed to parse review: {e}")
            return None
