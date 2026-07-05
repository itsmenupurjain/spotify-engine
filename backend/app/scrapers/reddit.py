"""
Reddit scraper — fetches Spotify discovery-related posts and comments via PRAW.
Targets 5 subreddits with 10 search queries.
"""

import logging
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any

from app.scrapers.base_scraper import BaseScraper
from app.config import settings

logger = logging.getLogger(__name__)

TARGET_SUBREDDITS = [
    "spotify",
    "Music",
    "ifyoulikeblank",
    "SpotifyPlaylists",
    "audiophile",
]

SEARCH_QUERIES = [
    "discover weekly not working",
    "spotify recommendations same songs",
    "sick of same music spotify",
    "can't find new music spotify",
    "spotify algorithm broken",
    "discover weekly stale",
    "release radar useless",
    "spotify keeps repeating",
    "how to discover new music spotify",
    "spotify used to recommend better",
]


class RedditScraper(BaseScraper):
    """Scraper for Reddit posts and comments about Spotify discovery."""

    SOURCE_NAME = "reddit"

    def __init__(self, posts_per_query: int = 10, top_comments: int = 10):
        super().__init__()
        self.posts_per_query = posts_per_query
        self.top_comments = top_comments

    async def scrape(self) -> List[Dict[str, Any]]:
        """Fetch Reddit posts and top comments using PRAW."""
        try:
            import praw
        except ImportError:
            logger.error("praw not installed. Run: pip install praw")
            return []

        if not settings.reddit_client_id or not settings.reddit_client_secret:
            logger.error("[reddit] Reddit API credentials not configured")
            return []

        reddit = praw.Reddit(
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            user_agent=settings.reddit_user_agent,
        )

        all_entries = []

        for subreddit_name in TARGET_SUBREDDITS:
            try:
                subreddit = reddit.subreddit(subreddit_name)

                for query in SEARCH_QUERIES:
                    try:
                        results = await self._retry_with_backoff(
                            self._search_subreddit, subreddit, query
                        )

                        for post in results:
                            # Parse the post itself
                            post_entry = self._parse_post(post, subreddit_name)
                            if post_entry:
                                all_entries.append(post_entry)

                            # Parse top comments
                            try:
                                post.comments.replace_more(limit=0)
                                top_comments = sorted(
                                    post.comments.list(),
                                    key=lambda c: c.score,
                                    reverse=True
                                )[:self.top_comments]

                                for comment in top_comments:
                                    if comment.score > 5:
                                        comment_entry = self._parse_comment(
                                            comment, post, subreddit_name
                                        )
                                        if comment_entry:
                                            all_entries.append(comment_entry)
                            except Exception as e:
                                logger.warning(f"[reddit] Failed to parse comments: {e}")

                    except Exception as e:
                        logger.warning(f"[reddit] Query '{query}' in r/{subreddit_name} failed: {e}")

                logger.info(f"[reddit] Fetched from r/{subreddit_name}: {sum(1 for e in all_entries if e.get('subreddit') == subreddit_name)} entries")

            except Exception as e:
                logger.error(f"[reddit] Error accessing r/{subreddit_name}: {e}")
                self.stats["entries_failed"] += 1

        return all_entries

    async def _search_subreddit(self, subreddit, query: str):
        """Search subreddit (runs in executor for sync PRAW)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: list(subreddit.search(query, sort="relevance", time_filter="year", limit=self.posts_per_query)),
        )

    def _parse_post(self, post, subreddit_name: str) -> Dict[str, Any]:
        """Parse a Reddit post into RawReview schema."""
        try:
            body = post.selftext or post.title
            if not body or len(body.strip()) < 20:
                return None

            return {
                "source": "reddit",
                "external_id": f"reddit_post_{post.id}",
                "rating": None,
                "title": post.title,
                "body": body,
                "author_hash": self._hash_author(str(post.author) if post.author else "deleted"),
                "published_at": datetime.fromtimestamp(post.created_utc, tz=timezone.utc),
                "engagement_score": post.score,
                "raw_url": f"https://reddit.com{post.permalink}",
                "language": None,
                "subreddit": subreddit_name,
                "post_title": post.title,
                "post_score": post.score,
                "is_comment": False,
            }
        except Exception as e:
            logger.error(f"[reddit] Failed to parse post: {e}")
            return None

    def _parse_comment(self, comment, post, subreddit_name: str) -> Dict[str, Any]:
        """Parse a Reddit comment into RawReview schema."""
        try:
            body = comment.body
            if not body or len(body.strip()) < 20 or body == "[deleted]":
                return None

            return {
                "source": "reddit",
                "external_id": f"reddit_comment_{comment.id}",
                "rating": None,
                "title": None,
                "body": body,
                "author_hash": self._hash_author(str(comment.author) if comment.author else "deleted"),
                "published_at": datetime.fromtimestamp(comment.created_utc, tz=timezone.utc),
                "engagement_score": comment.score,
                "raw_url": f"https://reddit.com{comment.permalink}",
                "language": None,
                "subreddit": subreddit_name,
                "post_title": post.title,
                "post_score": post.score,
                "comment_score": comment.score,
                "is_comment": True,
                "parent_post_id": f"reddit_post_{post.id}",
            }
        except Exception as e:
            logger.error(f"[reddit] Failed to parse comment: {e}")
            return None
