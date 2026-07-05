"""
Spotify Community Forum scraper — Playwright-based scraper for community.spotify.com.
Targets Music Recommendations, Discover Weekly, and Suggestions boards.
"""

import logging
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any

from app.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

TARGET_BOARDS = [
    {
        "name": "Music Recommendations",
        "url": "https://community.spotify.com/t5/Music/ct-p/Music",
    },
    {
        "name": "Suggestions",
        "url": "https://community.spotify.com/t5/Live-Ideas/idb-p/ideas_reimagination",
    },
]

SEARCH_TERMS = [
    "discover weekly",
    "recommendations",
    "algorithm",
    "discovery",
    "release radar",
    "same songs",
    "new music",
]


class CommunityForumScraper(BaseScraper):
    """Scraper for Spotify Community Forums using Playwright."""

    SOURCE_NAME = "spotify_community"

    def __init__(self, max_threads: int = 200):
        super().__init__()
        self.max_threads = max_threads

    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape Spotify Community Forums using Playwright.
        JS-rendered content requires a full browser context.
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error("playwright not installed. Run: pip install playwright && playwright install")
            return []

        all_entries = []

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                page = await context.new_page()

                for search_term in SEARCH_TERMS:
                    try:
                        search_url = (
                            f"https://community.spotify.com/t5/forums/searchpage"
                            f"/tab/message?filter=includeForums&q={search_term}"
                            f"&include_forums=true&sort_by=relevance"
                        )

                        await page.goto(search_url, wait_until="networkidle", timeout=15000)
                        await asyncio.sleep(2)

                        # Extract thread links from search results
                        thread_links = await page.evaluate("""
                            () => {
                                const links = document.querySelectorAll('.lia-link-navigation');
                                return Array.from(links).map(a => ({
                                    url: a.href,
                                    title: a.textContent.trim()
                                })).filter(l => l.url.includes('/t5/') && l.title.length > 10);
                            }
                        """)

                        # Visit each thread
                        for link_data in thread_links[:self.max_threads // len(SEARCH_TERMS)]:
                            try:
                                entry = await self._scrape_thread(page, link_data)
                                if entry:
                                    all_entries.append(entry)
                            except Exception as e:
                                logger.warning(f"[community] Failed to scrape thread: {e}")

                        logger.info(f"[community] Search '{search_term}': found {len(thread_links)} threads")

                    except Exception as e:
                        logger.warning(f"[community] Search for '{search_term}' failed: {e}")

                await browser.close()

        except Exception as e:
            logger.error(f"[community] Playwright error: {e}")

        return all_entries

    async def _scrape_thread(self, page, link_data: dict) -> Dict[str, Any]:
        """Scrape a single community forum thread."""
        url = link_data.get("url", "")
        if not url or "community.spotify.com" not in url:
            return None

        await page.goto(url, wait_until="networkidle", timeout=10000)
        await asyncio.sleep(1)

        # Extract thread content
        thread_data = await page.evaluate("""
            () => {
                const body = document.querySelector('.lia-message-body-content');
                const kudos = document.querySelector('.MessageKudosCount');
                const replies = document.querySelector('.lia-component-messages-count');
                const status = document.querySelector('.lia-message-status-label');
                const date = document.querySelector('.DateTime');

                // Get reply bodies
                const replyElements = document.querySelectorAll('.lia-message-body-content');
                const replyBodies = Array.from(replyElements).slice(1, 11).map(el => el.textContent.trim());

                return {
                    body: body ? body.textContent.trim() : '',
                    kudos: kudos ? parseInt(kudos.textContent) || 0 : 0,
                    replyCount: replies ? parseInt(replies.textContent) || 0 : 0,
                    status: status ? status.textContent.trim() : null,
                    date: date ? date.getAttribute('datetime') || date.textContent.trim() : null,
                    replies: replyBodies
                };
            }
        """)

        if not thread_data.get("body") or len(thread_data["body"]) < 20:
            return None

        # Combine thread body with reply bodies for richer signal
        full_body = thread_data["body"]
        if thread_data.get("replies"):
            full_body += "\n\n---REPLIES---\n" + "\n---\n".join(thread_data["replies"][:5])

        return {
            "source": "spotify_community",
            "external_id": f"community_{hash(url) % 10**12}",
            "rating": None,
            "title": link_data.get("title", ""),
            "body": full_body[:4000],  # Truncate very long threads
            "author_hash": self._hash_author(f"community_user_{hash(url)}"),
            "published_at": self._parse_date(thread_data.get("date")),
            "engagement_score": thread_data.get("kudos", 0),
            "raw_url": url,
            "language": None,
            "reply_count": thread_data.get("replyCount", 0),
            "kudos_count": thread_data.get("kudos", 0),
            "thread_status": thread_data.get("status"),
        }

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string from community forum."""
        if not date_str:
            return datetime.now(timezone.utc)
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return datetime.now(timezone.utc)
