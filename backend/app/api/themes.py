"""
Themes endpoints — list all themes and deep-dive into individual themes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID

from app.database import get_db
from app.models.theme import Theme, ReviewThemeMapping
from app.models.classified_review import ClassifiedReview
from app.models.raw_review import RawReview

router = APIRouter()


@router.get("/themes")
async def list_themes(db: AsyncSession = Depends(get_db)):
    """List all themes with summary stats."""
    query = select(Theme).order_by(Theme.review_count.desc())
    result = await db.execute(query)
    themes = result.scalars().all()

    return {
        "themes": [
            {
                "id": str(t.id),
                "cluster_id": t.cluster_id,
                "theme_name": t.theme_name,
                "theme_description": t.theme_description,
                "representative_quote": t.representative_quote,
                "review_count": t.review_count,
                "cross_source_count": t.cross_source_count,
                "confidence_level": t.confidence_level,
                "trend_direction": t.trend_direction,
            }
            for t in themes
        ],
        "total": len(themes),
    }


@router.get("/themes/{theme_id}")
async def get_theme(theme_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a single theme with full breakdown — reviews by source, segment, sentiment, trend, quotes."""
    theme = await db.get(Theme, theme_id)
    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found")

    # Get reviews linked to this theme
    reviews_query = (
        select(ClassifiedReview, RawReview)
        .join(ReviewThemeMapping, ReviewThemeMapping.review_id == ClassifiedReview.id)
        .join(RawReview, ClassifiedReview.raw_review_id == RawReview.id)
        .where(ReviewThemeMapping.theme_id == theme_id)
        .order_by(ReviewThemeMapping.similarity_score.desc())
    )
    result = await db.execute(reviews_query)
    review_rows = result.all()

    # Aggregate by source
    source_counts = {}
    segment_counts = {}
    sentiment_counts = {}
    monthly_counts = {}
    top_quotes = []

    for classified, raw in review_rows:
        # Source breakdown
        source_counts[raw.source] = source_counts.get(raw.source, 0) + 1

        # Segment breakdown
        seg = classified.user_segment_signal or "unclear"
        segment_counts[seg] = segment_counts.get(seg, 0) + 1

        # Sentiment breakdown
        sent = classified.sentiment or "neutral"
        sentiment_counts[sent] = sentiment_counts.get(sent, 0) + 1

        # Monthly trend
        if raw.published_at:
            month_key = raw.published_at.strftime("%Y-%m")
            monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1

        # Collect quotes (top 10)
        if len(top_quotes) < 10 and classified.key_frustration_phrase:
            top_quotes.append({
                "quote": classified.key_frustration_phrase,
                "full_body": raw.body[:500],
                "source": raw.source,
                "date": raw.published_at.isoformat() if raw.published_at else None,
                "rating": raw.rating,
                "sentiment": classified.sentiment,
                "segment": classified.user_segment_signal,
            })

    return {
        "id": str(theme.id),
        "theme_name": theme.theme_name,
        "theme_description": theme.theme_description,
        "representative_quote": theme.representative_quote,
        "review_count": theme.review_count,
        "cross_source_count": theme.cross_source_count,
        "confidence_level": theme.confidence_level,
        "trend_direction": theme.trend_direction,
        "source_breakdown": source_counts,
        "segment_breakdown": segment_counts,
        "sentiment_breakdown": sentiment_counts,
        "monthly_trend": dict(sorted(monthly_counts.items())),
        "top_quotes": top_quotes,
    }
