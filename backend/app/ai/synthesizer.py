"""
Cross-Source Synthesizer — aggregates and caches dashboard intelligence data.
Implements spec §4.3: daily batch job computing theme/segment/sentiment aggregations.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct

from app.models.classified_review import ClassifiedReview
from app.models.raw_review import RawReview
from app.models.theme import Theme, ReviewThemeMapping
from app.models.synthesis_cache import SynthesisCache

logger = logging.getLogger(__name__)


class Synthesizer:
    """Computes and caches cross-source synthesis for dashboard performance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def refresh_all(self) -> Dict[str, Any]:
        """Refresh all synthesis cache entries."""
        results = {}

        try:
            results["theme_frequency_by_source"] = await self._theme_frequency_by_source()
            results["theme_frequency_by_segment"] = await self._theme_frequency_by_segment()
            results["top_unmet_needs"] = await self._top_unmet_needs()
            results["sentiment_by_source"] = await self._sentiment_by_source()
            results["segment_distribution"] = await self._segment_distribution()
            results["dashboard_summary"] = await self._dashboard_summary()

            logger.info("Synthesis cache fully refreshed")
        except Exception as e:
            logger.error(f"Synthesis refresh failed: {e}")

        return results

    async def _cache_result(self, cache_key: str, data: Any):
        """Store or update a synthesis cache entry."""
        existing = await self.db.execute(
            select(SynthesisCache).where(SynthesisCache.cache_key == cache_key)
        )
        cache_entry = existing.scalar_one_or_none()

        if cache_entry:
            cache_entry.data = data
            cache_entry.generated_at = datetime.now(timezone.utc)
        else:
            cache_entry = SynthesisCache(
                cache_key=cache_key,
                data=data,
            )
            self.db.add(cache_entry)

        await self.db.flush()

    async def _theme_frequency_by_source(self) -> Dict:
        """How often each theme appears per source."""
        query = (
            select(
                Theme.theme_name,
                RawReview.source,
                func.count().label("count"),
            )
            .join(ReviewThemeMapping, ReviewThemeMapping.theme_id == Theme.id)
            .join(ClassifiedReview, ClassifiedReview.id == ReviewThemeMapping.review_id)
            .join(RawReview, RawReview.id == ClassifiedReview.raw_review_id)
            .group_by(Theme.theme_name, RawReview.source)
        )

        result = await self.db.execute(query)
        data = {}
        for theme_name, source, count in result.all():
            if theme_name not in data:
                data[theme_name] = {}
            data[theme_name][source] = count

        await self._cache_result("theme_frequency_by_source", data)
        return data

    async def _theme_frequency_by_segment(self) -> Dict:
        """Which segments mention which themes most."""
        query = (
            select(
                Theme.theme_name,
                ClassifiedReview.user_segment_signal,
                func.count().label("count"),
            )
            .join(ReviewThemeMapping, ReviewThemeMapping.theme_id == Theme.id)
            .join(ClassifiedReview, ClassifiedReview.id == ReviewThemeMapping.review_id)
            .group_by(Theme.theme_name, ClassifiedReview.user_segment_signal)
        )

        result = await self.db.execute(query)
        data = {}
        for theme_name, segment, count in result.all():
            if theme_name not in data:
                data[theme_name] = {}
            data[theme_name][segment or "unclear"] = count

        await self._cache_result("theme_frequency_by_segment", data)
        return data

    async def _top_unmet_needs(self) -> list:
        """Top 5 unmet needs by frequency."""
        query = (
            select(
                ClassifiedReview.unmet_need,
                func.count().label("count"),
            )
            .where(ClassifiedReview.unmet_need.isnot(None))
            .where(ClassifiedReview.classification_failed == False)
            .group_by(ClassifiedReview.unmet_need)
            .order_by(func.count().desc())
            .limit(5)
        )

        result = await self.db.execute(query)
        data = [{"need": row[0], "count": row[1]} for row in result.all()]

        await self._cache_result("top_unmet_needs", data)
        return data

    async def _sentiment_by_source(self) -> Dict:
        """Sentiment distribution per source."""
        query = (
            select(
                RawReview.source,
                ClassifiedReview.sentiment,
                func.count().label("count"),
            )
            .join(RawReview, RawReview.id == ClassifiedReview.raw_review_id)
            .where(ClassifiedReview.classification_failed == False)
            .group_by(RawReview.source, ClassifiedReview.sentiment)
        )

        result = await self.db.execute(query)
        data = {}
        for source, sentiment, count in result.all():
            if source not in data:
                data[source] = {}
            data[source][sentiment or "unknown"] = count

        await self._cache_result("sentiment_by_source", data)
        return data

    async def _segment_distribution(self) -> Dict:
        """Review count per user segment."""
        query = (
            select(
                ClassifiedReview.user_segment_signal,
                func.count().label("count"),
            )
            .where(ClassifiedReview.classification_failed == False)
            .group_by(ClassifiedReview.user_segment_signal)
        )

        result = await self.db.execute(query)
        data = {row[0] or "unclear": row[1] for row in result.all()}

        await self._cache_result("segment_distribution", data)
        return data

    async def _dashboard_summary(self) -> Dict:
        """Full dashboard summary (powers the Intelligence Home view)."""
        total_raw = (await self.db.execute(
            select(func.count()).select_from(RawReview)
        )).scalar() or 0

        total_classified = (await self.db.execute(
            select(func.count()).select_from(ClassifiedReview)
            .where(ClassifiedReview.classification_failed == False)
        )).scalar() or 0

        source_counts = dict((await self.db.execute(
            select(RawReview.source, func.count())
            .group_by(RawReview.source)
        )).all())

        last_updated = (await self.db.execute(
            select(func.max(RawReview.ingested_at))
        )).scalar()

        # Top 6 themes
        themes = (await self.db.execute(
            select(Theme).order_by(Theme.review_count.desc()).limit(6)
        )).scalars().all()

        # Top 5 unmet needs
        needs_result = await self.db.execute(
            select(
                ClassifiedReview.unmet_need,
                func.count().label("cnt"),
            )
            .where(ClassifiedReview.unmet_need.isnot(None))
            .where(ClassifiedReview.classification_failed == False)
            .group_by(ClassifiedReview.unmet_need)
            .order_by(func.count().desc())
            .limit(5)
        )
        top_unmet_needs = [{"need": row[0], "count": row[1]} for row in needs_result.all()]

        # Segment distribution
        segment_result = await self.db.execute(
            select(
                ClassifiedReview.user_segment_signal,
                func.count().label("cnt"),
            )
            .where(ClassifiedReview.classification_failed == False)
            .group_by(ClassifiedReview.user_segment_signal)
        )
        segment_distribution = {row[0] or "unclear": row[1] for row in segment_result.all()}

        # Sentiment by source
        sentiment_result = await self.db.execute(
            select(
                RawReview.source,
                ClassifiedReview.sentiment,
                func.count().label("cnt"),
            )
            .join(RawReview, ClassifiedReview.raw_review_id == RawReview.id)
            .where(ClassifiedReview.classification_failed == False)
            .group_by(RawReview.source, ClassifiedReview.sentiment)
        )
        sentiment_by_source = {}
        for source, sentiment, count in sentiment_result.all():
            if source not in sentiment_by_source:
                sentiment_by_source[source] = {}
            sentiment_by_source[source][sentiment or "unknown"] = count

        summary = {
            "total_raw_reviews": total_raw,
            "total_classified_reviews": total_classified,
            "sources_active": len(source_counts),
            "source_counts": source_counts,
            "last_updated": last_updated.isoformat() if last_updated else None,
            "top_themes": [
                {
                    "id": str(t.id),
                    "name": t.theme_name,
                    "description": t.theme_description,
                    "review_count": t.review_count,
                    "cross_source_count": t.cross_source_count,
                    "confidence_level": t.confidence_level,
                    "trend_direction": t.trend_direction,
                    "representative_quote": t.representative_quote,
                }
                for t in themes
            ],
            "top_unmet_needs": top_unmet_needs,
            "segment_distribution": segment_distribution,
            "sentiment_by_source": sentiment_by_source,
        }

        await self._cache_result("dashboard_summary", summary)
        return summary
