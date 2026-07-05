"""
Pipeline Scheduler — APScheduler-based cron jobs for automated data pipeline.

Jobs (from spec §8.1):
  - ingest_all_sources    : Weekly (Sunday 2am UTC)
  - classify_new_reviews  : Daily (1am UTC)
  - update_clusters       : Weekly (Monday 4am UTC)
  - refresh_synthesis_cache: Daily (3am UTC)
  - embed_new_reviews     : Daily (2am UTC)
  - health_check          : Every 15 minutes
"""

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="UTC")


def get_scheduler() -> AsyncIOScheduler:
    return scheduler


# ─── Job Functions ───────────────────────────────────────────────────────────

async def job_ingest_all_sources():
    """Weekly: Ingest new reviews from all 5 sources."""
    logger.info("🔄 [SCHEDULER] Starting ingest_all_sources job...")
    async with AsyncSessionLocal() as db:
        try:
            from app.pipeline.orchestrator import PipelineOrchestrator
            orchestrator = PipelineOrchestrator(db)
            results = await orchestrator.run(source=None)
            await db.commit()
            logger.info(f"✅ [SCHEDULER] ingest_all_sources complete: {results}")
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ [SCHEDULER] ingest_all_sources failed: {e}")


async def job_classify_new_reviews():
    """Daily: Run AI classification on unprocessed reviews."""
    logger.info("🤖 [SCHEDULER] Starting classify_new_reviews job...")
    async with AsyncSessionLocal() as db:
        try:
            from sqlalchemy import select
            from app.models.raw_review import RawReview
            from app.models.classified_review import ClassifiedReview
            from app.ai.classifier import AIClassifier

            # Get unclassified relevant reviews
            result = await db.execute(
                select(RawReview)
                .where(RawReview.is_relevant == True)
                .where(
                    ~RawReview.id.in_(
                        select(ClassifiedReview.raw_review_id)
                    )
                )
                .limit(500)  # Process up to 500 per daily run
            )
            unclassified = result.scalars().all()

            if not unclassified:
                logger.info("[SCHEDULER] No unclassified reviews found.")
                return

            logger.info(f"[SCHEDULER] Classifying {len(unclassified)} reviews...")

            classifier = AIClassifier()
            entries = [
                {"id": str(r.id), "body": r.body, "source": r.source, "rating": r.rating}
                for r in unclassified
            ]
            classifications = await classifier.classify_batch(entries)

            # Store results
            stored = 0
            for entry, classification in zip(unclassified, classifications):
                if classification.get("classification_failed"):
                    continue
                from app.models.classified_review import ClassifiedReview
                cr = ClassifiedReview(
                    raw_review_id=entry.id,
                    is_discovery_relevant=classification.get("is_discovery_relevant"),
                    primary_complaint_category=classification.get("primary_complaint_category"),
                    secondary_complaint_category=classification.get("secondary_complaint_category"),
                    user_segment_signal=classification.get("user_segment_signal"),
                    sentiment=classification.get("sentiment"),
                    sentiment_score=classification.get("sentiment_score"),
                    discovery_intent=classification.get("discovery_intent"),
                    repetition_behavior_mentioned=classification.get("repetition_behavior_mentioned"),
                    key_frustration_phrase=classification.get("key_frustration_phrase"),
                    unmet_need=classification.get("unmet_need"),
                    jtbd_statement=classification.get("jtbd_statement"),
                    confidence_score=classification.get("confidence_score"),
                    detected_language=classification.get("language"),
                    source_weight=entry.source_weight,
                    recency_score=entry.recency_score,
                    classification_model=classification.get("classification_model", "claude-sonnet-4-6"),
                    classification_failed=False,
                    embedding_pending=True,
                )
                db.add(cr)
                stored += 1

            await db.commit()
            logger.info(f"✅ [SCHEDULER] classify_new_reviews: stored {stored} classifications")

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ [SCHEDULER] classify_new_reviews failed: {e}")


async def job_embed_new_reviews():
    """Daily: Generate embeddings for newly classified reviews."""
    logger.info("🔢 [SCHEDULER] Starting embed_new_reviews job...")
    async with AsyncSessionLocal() as db:
        try:
            from sqlalchemy import select
            from app.models.classified_review import ClassifiedReview
            from app.models.raw_review import RawReview
            from app.ai.embedder import Embedder

            # Get classified reviews without embeddings
            result = await db.execute(
                select(ClassifiedReview, RawReview)
                .join(RawReview, ClassifiedReview.raw_review_id == RawReview.id)
                .where(ClassifiedReview.embedding_pending == True)
                .where(ClassifiedReview.classification_failed == False)
                .limit(200)  # Process up to 200 per daily run
            )
            rows = result.all()

            if not rows:
                logger.info("[SCHEDULER] No reviews pending embedding.")
                return

            logger.info(f"[SCHEDULER] Embedding {len(rows)} reviews...")

            embedder = Embedder()
            texts = [raw.body for _, raw in rows]
            embeddings = await embedder.embed_texts(texts)

            updated = 0
            for (classified, _), embedding in zip(rows, embeddings):
                if embedding:
                    classified.embedding = embedding
                    classified.embedding_pending = False
                    updated += 1

            await db.commit()
            logger.info(f"✅ [SCHEDULER] embed_new_reviews: embedded {updated} reviews")

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ [SCHEDULER] embed_new_reviews failed: {e}")


async def job_update_clusters():
    """Weekly: Re-cluster themes with new data."""
    logger.info("🔮 [SCHEDULER] Starting update_clusters job...")
    async with AsyncSessionLocal() as db:
        try:
            from sqlalchemy import select
            from app.models.classified_review import ClassifiedReview
            from app.models.raw_review import RawReview
            from app.models.theme import Theme, ReviewThemeMapping
            from app.ai.clusterer import ThemeClusterer

            # Get all classified reviews with frustration phrases
            result = await db.execute(
                select(ClassifiedReview, RawReview)
                .join(RawReview, ClassifiedReview.raw_review_id == RawReview.id)
                .where(ClassifiedReview.key_frustration_phrase.isnot(None))
                .where(ClassifiedReview.classification_failed == False)
            )
            rows = result.all()

            if len(rows) < 50:
                logger.warning("[SCHEDULER] Not enough entries for clustering.")
                return

            entries = [
                {
                    "id": str(cr.id),
                    "key_frustration_phrase": cr.key_frustration_phrase,
                    "source": raw.source,
                }
                for cr, raw in rows
            ]

            clusterer = ThemeClusterer()
            themes = await clusterer.cluster_and_label(entries)

            # Clear old mappings and update themes
            for theme_data in themes:
                # Upsert theme
                existing = await db.execute(
                    select(Theme).where(Theme.cluster_id == theme_data["cluster_id"])
                )
                theme = existing.scalar_one_or_none()

                if theme:
                    theme.theme_name = theme_data.get("theme_name", theme.theme_name)
                    theme.theme_description = theme_data.get("theme_description")
                    theme.representative_quote = theme_data.get("representative_quote")
                    theme.review_count = theme_data.get("review_count", 0)
                    theme.cross_source_count = theme_data.get("cross_source_count", 0)
                    theme.confidence_level = theme_data.get("confidence_level")
                    theme.updated_at = datetime.now(timezone.utc)
                else:
                    theme = Theme(
                        cluster_id=theme_data["cluster_id"],
                        theme_name=theme_data.get("theme_name", f"Theme {theme_data['cluster_id']+1}"),
                        theme_description=theme_data.get("theme_description"),
                        representative_quote=theme_data.get("representative_quote"),
                        review_count=theme_data.get("review_count", 0),
                        cross_source_count=theme_data.get("cross_source_count", 0),
                        confidence_level=theme_data.get("confidence_level"),
                        trend_direction="stable",
                    )
                    db.add(theme)

                await db.flush()

                # Create review-theme mappings
                for review_id in theme_data.get("review_ids", []):
                    mapping = ReviewThemeMapping(
                        review_id=review_id,
                        theme_id=theme.id,
                        similarity_score=1.0,
                    )
                    db.add(mapping)

            await db.commit()
            logger.info(f"✅ [SCHEDULER] update_clusters: processed {len(themes)} themes")

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ [SCHEDULER] update_clusters failed: {e}")


async def job_refresh_synthesis_cache():
    """Daily: Recompute all aggregations for dashboard."""
    logger.info("📊 [SCHEDULER] Starting refresh_synthesis_cache job...")
    async with AsyncSessionLocal() as db:
        try:
            from app.ai.synthesizer import Synthesizer
            synthesizer = Synthesizer(db)
            await synthesizer.refresh_all()
            await db.commit()
            logger.info("✅ [SCHEDULER] refresh_synthesis_cache complete")
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ [SCHEDULER] refresh_synthesis_cache failed: {e}")


async def job_health_check():
    """Every 15 minutes: Check pipeline status and alert on failures."""
    async with AsyncSessionLocal() as db:
        try:
            from sqlalchemy import select, func, text
            from app.models.pipeline_run import PipelineRun
            from app.models.classified_review import ClassifiedReview
            from app.services.monitoring import MonitoringService

            monitor = MonitoringService(db)
            await monitor.run_health_check()

        except Exception as e:
            logger.error(f"❌ [SCHEDULER] health_check failed: {e}")


# ─── Scheduler Setup ─────────────────────────────────────────────────────────

def configure_scheduler():
    """Register all cron jobs with APScheduler."""

    # ingest_all_sources — Weekly (Sunday 2am UTC)
    scheduler.add_job(
        job_ingest_all_sources,
        CronTrigger(day_of_week="sun", hour=2, minute=0, timezone="UTC"),
        id="ingest_all_sources",
        name="Ingest All Sources",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    # classify_new_reviews — Daily (1am UTC)
    scheduler.add_job(
        job_classify_new_reviews,
        CronTrigger(hour=1, minute=0, timezone="UTC"),
        id="classify_new_reviews",
        name="Classify New Reviews",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    # embed_new_reviews — Daily (2am UTC)
    scheduler.add_job(
        job_embed_new_reviews,
        CronTrigger(hour=2, minute=0, timezone="UTC"),
        id="embed_new_reviews",
        name="Embed New Reviews",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    # refresh_synthesis_cache — Daily (3am UTC)
    scheduler.add_job(
        job_refresh_synthesis_cache,
        CronTrigger(hour=3, minute=0, timezone="UTC"),
        id="refresh_synthesis_cache",
        name="Refresh Synthesis Cache",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    # update_clusters — Weekly (Monday 4am UTC)
    scheduler.add_job(
        job_update_clusters,
        CronTrigger(day_of_week="mon", hour=4, minute=0, timezone="UTC"),
        id="update_clusters",
        name="Update Theme Clusters",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    # health_check — Every 15 minutes
    scheduler.add_job(
        job_health_check,
        IntervalTrigger(minutes=15),
        id="health_check",
        name="Health Check",
        replace_existing=True,
        misfire_grace_time=300,
    )

    logger.info("✅ All pipeline jobs scheduled:")
    for job in scheduler.get_jobs():
        logger.info(f"   • {job.name} (id={job.id})")
