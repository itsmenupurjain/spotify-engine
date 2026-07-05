"""
Synthesis endpoint — pre-aggregated intelligence summary for the home dashboard.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.synthesis_cache import SynthesisCache
from app.models.raw_review import RawReview
from app.models.classified_review import ClassifiedReview
from app.models.theme import Theme

router = APIRouter()


@router.get("/synthesis/summary")
async def get_summary(db: AsyncSession = Depends(get_db)):
    """
    Top-level intelligence summary for the home dashboard.
    Returns cached synthesis data or computes live if cache is stale.
    """
    # Try cache first
    cache_query = select(SynthesisCache).where(SynthesisCache.cache_key == "dashboard_summary")
    result = await db.execute(cache_query)
    cached = result.scalar_one_or_none()

    if cached and cached.data:
        return cached.data

    # Compute live summary
    # Total reviews
    total_raw = await db.execute(select(func.count()).select_from(RawReview))
    total_classified = await db.execute(
        select(func.count()).select_from(ClassifiedReview)
        .where(ClassifiedReview.classification_failed == False)
    )

    # Source counts
    source_query = (
        select(RawReview.source, func.count().label("cnt"))
        .group_by(RawReview.source)
    )
    source_result = await db.execute(source_query)
    source_counts = {row[0]: row[1] for row in source_result.all()}

    # Sentiment distribution by source
    sentiment_query = (
        select(
            RawReview.source,
            ClassifiedReview.sentiment,
            func.count().label("cnt")
        )
        .join(RawReview, ClassifiedReview.raw_review_id == RawReview.id)
        .where(ClassifiedReview.classification_failed == False)
        .group_by(RawReview.source, ClassifiedReview.sentiment)
    )
    sentiment_result = await db.execute(sentiment_query)
    sentiment_by_source = {}
    for source, sentiment, count in sentiment_result.all():
        if source not in sentiment_by_source:
            sentiment_by_source[source] = {}
        sentiment_by_source[source][sentiment or "unknown"] = count

    # Segment distribution
    segment_query = (
        select(
            ClassifiedReview.user_segment_signal,
            func.count().label("cnt")
        )
        .where(ClassifiedReview.classification_failed == False)
        .group_by(ClassifiedReview.user_segment_signal)
    )
    segment_result = await db.execute(segment_query)
    segment_distribution = {row[0] or "unclear": row[1] for row in segment_result.all()}

    # Top unmet needs
    needs_query = (
        select(
            ClassifiedReview.unmet_need,
            func.count().label("cnt")
        )
        .where(ClassifiedReview.unmet_need.isnot(None))
        .where(ClassifiedReview.classification_failed == False)
        .group_by(ClassifiedReview.unmet_need)
        .order_by(func.count().desc())
        .limit(5)
    )
    needs_result = await db.execute(needs_query)
    top_unmet_needs = [{"need": row[0], "count": row[1]} for row in needs_result.all()]

    # Top themes
    themes_query = select(Theme).order_by(Theme.review_count.desc()).limit(6)
    themes_result = await db.execute(themes_query)
    top_themes = [
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
        for t in themes_result.scalars().all()
    ]

    # Last updated timestamp
    last_updated_query = select(func.max(RawReview.ingested_at))
    last_updated_result = await db.execute(last_updated_query)
    last_updated = last_updated_result.scalar()

    summary = {
        "total_raw_reviews": total_raw.scalar() or 0,
        "total_classified_reviews": total_classified.scalar() or 0,
        "sources_active": len(source_counts),
        "source_counts": source_counts,
        "last_updated": last_updated.isoformat() if last_updated else None,
        "top_themes": top_themes,
        "top_unmet_needs": top_unmet_needs,
        "segment_distribution": segment_distribution,
        "sentiment_by_source": sentiment_by_source,
    }

    return summary
