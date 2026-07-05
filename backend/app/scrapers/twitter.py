"""
Twitter/X scraper — fetches Spotify discovery-related tweets.
Primary: Twitter API v2 (Basic tier)
Fallback: Apify Twitter scraper
"""

import logging
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any

from app.scrapers.base_scraper import BaseScraper
from app.config import settings

logger = logging.getLogger(__name__)

SEARCH_QUERIES = [
    "spotify recommend same songs",
    "spotify discover weekly boring",
    "spotify algorithm bad",
    "can't find new music spotify",
    "spotify used to be better at recommendations",
    "@spotify discover weekly",
    "spotify playlist repetitive",
]


class TwitterScraper(BaseScraper):
    """Scraper for Twitter/X posts about Spotify discovery issues."""

    SOURCE_NAME = "twitter_x"

    def __init__(self, max_tweets: int = 500):
        super().__init__()
        self.max_tweets = max_tweets

    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Fetch tweets using Twitter API v2 or Apify fallback.
        English only, no retweets.
        """
        # Try official API first
        if settings.twitter_bearer_token:
            try:
                return await self._scrape_official_api()
            except Exception as e:
                logger.warning(f"[twitter] Official API failed: {e}. Trying Apify fallback...")

        # Fallback to Apify
        if settings.apify_api_token:
            try:
                return await self._scrape_apify()
            except Exception as e:
                logger.error(f"[twitter] Apify fallback also failed: {e}")

        logger.error("[twitter] No Twitter API credentials configured. Skipping.")
        return []

    async def _scrape_official_api(self) -> List[Dict[str, Any]]:
        """Scrape using Twitter API v2."""
        import httpx

        all_tweets = []
        tweets_per_query = self.max_tweets // len(SEARCH_QUERIES)

        headers = {
            "Authorization": f"Bearer {settings.twitter_bearer_token}",
        }

        async with httpx.AsyncClient() as client:
            for query in SEARCH_QUERIES:
                try:
                    # Twitter API v2 search endpoint
                    search_query = f"{query} -is:retweet lang:en"
                    params = {
                        "query": search_query,
                        "max_results": min(tweets_per_query, 100),
                        "tweet.fields": "created_at,public_metrics,author_id,lang",
                    }

                    response = await self._retry_with_backoff(
                        self._make_request, client, headers, params
                    )

                    if response and response.get("data"):
                        for tweet in response["data"]:
                            parsed = self._parse_tweet(tweet)
                            if parsed:
                                all_tweets.append(parsed)

                    logger.info(f"[twitter] Query '{query}': {len(response.get('data', []))} tweets")

                except Exception as e:
                    logger.warning(f"[twitter] Query '{query}' failed: {e}")

        return all_tweets

    async def _make_request(self, client, headers, params):
        """Make a request to Twitter API."""
        response = await client.get(
            "https://api.twitter.com/2/tweets/search/recent",
            headers=headers,
            params=params,
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()

    async def _scrape_apify(self) -> List[Dict[str, Any]]:
        """Scrape using Apify Twitter Scraper as fallback."""
        import httpx

        all_tweets = []

        async with httpx.AsyncClient() as client:
            for query in SEARCH_QUERIES:
                try:
                    # Start Apify actor run
                    run_input = {
                        "searchTerms": [query],
                        "maxTweets": self.max_tweets // len(SEARCH_QUERIES),
                        "language": "en",
                        "onlyVerifiedUsers": False,
                    }

                    response = await client.post(
                        "https://api.apify.com/v2/acts/apidojo~tweet-scraper/runs",
                        json=run_input,
                        params={"token": settings.apify_api_token},
                        timeout=30.0,
                    )
                    response.raise_for_status()
                    run_data = response.json()

                    # Wait for run to complete and fetch results
                    run_id = run_data.get("data", {}).get("id")
                    if run_id:
                        await asyncio.sleep(10)  # Wait for actor to process
                        results_response = await client.get(
                            f"https://api.apify.com/v2/actor-runs/{run_id}/dataset/items",
                            params={"token": settings.apify_api_token},
                            timeout=30.0,
                        )
                        if results_response.status_code == 200:
                            for item in results_response.json():
                                parsed = self._parse_apify_tweet(item)
                                if parsed:
                                    all_tweets.append(parsed)

                except Exception as e:
                    logger.warning(f"[twitter] Apify query '{query}' failed: {e}")

        return all_tweets

    def _parse_tweet(self, tweet: dict) -> Dict[str, Any]:
        """Parse a tweet from Twitter API v2 response."""
        try:
            text = tweet.get("text", "")
            if not text or len(text.strip()) < 20:
                return None

            metrics = tweet.get("public_metrics", {})

            return {
                "source": "twitter_x",
                "external_id": f"twitter_{tweet.get('id', '')}",
                "rating": None,
                "title": None,
                "body": text,
                "author_hash": self._hash_author(tweet.get("author_id", "unknown")),
                "published_at": self._parse_date(tweet.get("created_at")),
                "engagement_score": metrics.get("like_count", 0),
                "raw_url": f"https://x.com/i/status/{tweet.get('id', '')}",
                "language": tweet.get("lang", "en"),
                "like_count": metrics.get("like_count", 0),
                "retweet_count": metrics.get("retweet_count", 0),
            }
        except Exception as e:
            logger.error(f"[twitter] Failed to parse tweet: {e}")
            return None

    def _parse_apify_tweet(self, item: dict) -> Dict[str, Any]:
        """Parse a tweet from Apify scraper response."""
        try:
            text = item.get("full_text", item.get("text", ""))
            if not text or len(text.strip()) < 20:
                return None

            return {
                "source": "twitter_x",
                "external_id": f"twitter_{item.get('id_str', item.get('id', ''))}",
                "rating": None,
                "title": None,
                "body": text,
                "author_hash": self._hash_author(str(item.get("user", {}).get("id_str", "unknown"))),
                "published_at": self._parse_date(item.get("created_at")),
                "engagement_score": item.get("favorite_count", 0),
                "raw_url": f"https://x.com/i/status/{item.get('id_str', '')}",
                "language": item.get("lang", "en"),
                "like_count": item.get("favorite_count", 0),
                "retweet_count": item.get("retweet_count", 0),
            }
        except Exception as e:
            logger.error(f"[twitter] Failed to parse Apify tweet: {e}")
            return None

    def _parse_date(self, date_str: str) -> datetime:
        """Parse various date formats from Twitter."""
        if not date_str:
            return datetime.now(timezone.utc)
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            try:
                # Twitter's native date format
                from email.utils import parsedate_to_datetime
                return parsedate_to_datetime(date_str)
            except Exception:
                return datetime.now(timezone.utc)
