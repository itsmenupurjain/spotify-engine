"""
Pipeline Orchestrator — coordinates ingestion, cleaning, and storage.
Tracks run stats and supports single-source or all-source triggers.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.raw_review import RawReview
from app.models.pipeline_run import PipelineRun
from app.pipeline.cleaner import DataCleaner
from app.scrapers.app_store import AppStoreScraper
from app.scrapers.play_store import PlayStoreScraper
from app.scrapers.reddit import RedditScraper
from app.scrapers.community_forum import CommunityForumScraper
from app.scrapers.twitter import TwitterScraper

logger = logging.getLogger(__name__)

SCRAPERS = {
    "app_store": AppStoreScraper,
    "play_store": PlayStoreScraper,
    "reddit": RedditScraper,
    "spotify_community": CommunityForumScraper,
    "twitter_x": TwitterScraper,
}


class PipelineOrchestrator:
    """Orchestrates the full ingestion pipeline: scrape → clean → store."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run(self, source: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the ingestion pipeline for one or all sources.

        Args:
            source: Specific source to run, or None for all sources.

        Returns:
            Dict with pipeline run stats.
        """
        sources_to_run = [source] if source else list(SCRAPERS.keys())
        results = {}

        for src in sources_to_run:
            if src not in SCRAPERS:
                logger.warning(f"Unknown source: {src}")
                continue

            # Create pipeline run record
            run = PipelineRun(
                job_name=f"ingest_{src}",
                status="running",
            )
            self.db.add(run)
            await self.db.flush()

            try:
                result = await self._run_source(src)
                run.status = "completed"
                run.entries_processed = result.get("total_scraped", 0)
                run.entries_created = result.get("entries_stored", 0)
                run.entries_failed = result.get("entries_failed", 0)
                results[src] = result

            except Exception as e:
                logger.error(f"Pipeline failed for {src}: {e}")
                run.status = "failed"
                run.error_message = str(e)
                results[src] = {"error": str(e)}

            finally:
                run.completed_at = datetime.now(timezone.utc)
                if run.started_at and run.completed_at:
                    run.duration_seconds = (run.completed_at - run.started_at).total_seconds()

        return results

    async def _run_source(self, source: str) -> Dict[str, Any]:
        """Run pipeline for a single source: scrape → clean → store."""
        logger.info(f"[pipeline] Starting ingestion for {source}...")

        # 1. Scrape
        scraper_class = SCRAPERS[source]
        scraper = scraper_class()
        raw_entries = await scraper.run()

        if not raw_entries:
            logger.warning(f"[pipeline] No entries scraped from {source}")
            return {"total_scraped": 0, "entries_stored": 0, "entries_failed": 0}

        # 2. Clean
        cleaner = DataCleaner()
        relevant, excluded = cleaner.process_batch(raw_entries)

        # 3. Store relevant entries
        stored_count = 0
        failed_count = 0

        for entry in relevant:
            try:
                raw_review = RawReview(
                    source=entry.get("source"),
                    external_id=entry.get("external_id"),
                    rating=entry.get("rating"),
                    title=entry.get("title"),
                    body=entry.get("body"),
                    author_hash=entry.get("author_hash"),
                    published_at=entry.get("published_at"),
                    app_version=entry.get("app_version"),
                    country_code=entry.get("country_code"),
                    engagement_score=entry.get("engagement_score"),
                    raw_url=entry.get("raw_url"),
                    language=entry.get("language"),
                    is_relevant=True,
                    body_hash=entry.get("body_hash"),
                    source_weight=entry.get("source_weight"),
                    recency_score=entry.get("recency_score"),
                    processed_at=datetime.now(timezone.utc),
                    # Reddit extras
                    subreddit=entry.get("subreddit"),
                    post_title=entry.get("post_title"),
                    post_score=entry.get("post_score"),
                    comment_score=entry.get("comment_score"),
                    is_comment=entry.get("is_comment", False),
                    parent_post_id=entry.get("parent_post_id"),
                    # Forum extras
                    reply_count=entry.get("reply_count"),
                    kudos_count=entry.get("kudos_count"),
                    thread_status=entry.get("thread_status"),
                    # Twitter extras
                    like_count=entry.get("like_count"),
                    retweet_count=entry.get("retweet_count"),
                )
                self.db.add(raw_review)
                stored_count += 1
            except Exception as e:
                logger.warning(f"[pipeline] Failed to store entry: {e}")
                failed_count += 1

        # Store excluded entries (for audit trail)
        for entry in excluded:
            try:
                raw_review = RawReview(
                    source=entry.get("source"),
                    external_id=entry.get("external_id"),
                    body=entry.get("body", ""),
                    is_relevant=False,
                    exclusion_reason=entry.get("exclusion_reason"),
                    language=entry.get("language"),
                )
                self.db.add(raw_review)
            except Exception:
                pass  # Excluded entries are best-effort

        await self.db.flush()

        result = {
            "source": source,
            "total_scraped": len(raw_entries),
            "entries_relevant": len(relevant),
            "entries_excluded": len(excluded),
            "entries_stored": stored_count,
            "entries_failed": failed_count,
            "cleaner_stats": cleaner.get_stats(),
            "scraper_stats": scraper.get_stats(),
        }

        logger.info(f"[pipeline] {source}: scraped={len(raw_entries)}, stored={stored_count}, excluded={len(excluded)}")
        return result

    async def load_seed_data(self, seed_file_path: str) -> Dict[str, Any]:
        """
        Load seed data from JSON file into the database.
        Used for development and demos when live scraping isn't available.
        Handles raw_reviews, classified_reviews, themes, review_theme_mappings,
        and synthesis_cache entries.
        """
        import json
        from app.models.classified_review import ClassifiedReview
        from app.models.theme import Theme, ReviewThemeMapping
        from app.models.synthesis_cache import SynthesisCache

        with open(seed_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        raw_reviews = data.get("raw_reviews", [])
        classified_reviews = data.get("classified_reviews", [])
        themes_data = data.get("themes", [])
        mappings_data = data.get("review_theme_mappings", [])
        cache_data = data.get("synthesis_cache", [])

        # Map old IDs to new IDs
        id_map = {}
        classified_id_map = {}

        # Store raw reviews
        stored_raw = 0
        for entry in raw_reviews:
            old_id = entry.pop("id", None)
            raw_review = RawReview(**{k: v for k, v in entry.items() if hasattr(RawReview, k)})
            self.db.add(raw_review)
            await self.db.flush()
            if old_id:
                id_map[old_id] = raw_review.id
            stored_raw += 1

        # Store classified reviews
        stored_classified = 0
        for entry in classified_reviews:
            old_id = entry.pop("id", None)
            old_raw_id = entry.pop("raw_review_id", None)

            # Map to new raw_review_id
            if old_raw_id and old_raw_id in id_map:
                entry["raw_review_id"] = id_map[old_raw_id]
            else:
                continue  # Skip if we can't map to raw review

            # Remove fields not in model
            entry.pop("embedding", None)
            entry.pop("source_from_raw", None)
            classified = ClassifiedReview(**{k: v for k, v in entry.items() if hasattr(ClassifiedReview, k)})
            self.db.add(classified)
            await self.db.flush()
            if old_id:
                classified_id_map[old_id] = classified.id
            stored_classified += 1

        # Store themes
        stored_themes = 0
        theme_id_map = {}
        for entry in themes_data:
            old_id = entry.pop("id", None)
            theme = Theme(**{k: v for k, v in entry.items() if hasattr(Theme, k)})
            self.db.add(theme)
            await self.db.flush()
            if old_id:
                theme_id_map[old_id] = theme.id
            stored_themes += 1

        # Store review-theme mappings
        stored_mappings = 0
        for entry in mappings_data:
            old_review_id = entry.get("review_id")
            old_theme_id = entry.get("theme_id")

            new_review_id = classified_id_map.get(old_review_id)
            new_theme_id = theme_id_map.get(old_theme_id)

            if new_review_id and new_theme_id:
                mapping = ReviewThemeMapping(
                    review_id=new_review_id,
                    theme_id=new_theme_id,
                    similarity_score=entry.get("similarity_score", 1.0),
                )
                self.db.add(mapping)
                stored_mappings += 1

        # Store synthesis cache
        stored_cache = 0
        for entry in cache_data:
            cache_entry = SynthesisCache(
                cache_key=entry["cache_key"],
                data=entry["data"],
            )
            self.db.add(cache_entry)
            stored_cache += 1

        await self.db.flush()

        logger.info(
            f"[seed] Loaded {stored_raw} raw, {stored_classified} classified, "
            f"{stored_themes} themes, {stored_mappings} mappings, {stored_cache} cache entries"
        )
        return {
            "raw_reviews_loaded": stored_raw,
            "classified_reviews_loaded": stored_classified,
            "themes_loaded": stored_themes,
            "review_theme_mappings_loaded": stored_mappings,
            "synthesis_cache_loaded": stored_cache,
        }
