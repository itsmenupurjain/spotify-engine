"""
Opportunities endpoint — data for the 2x2 opportunity map (frequency × severity × cross-source).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.theme import Theme, ReviewThemeMapping
from app.models.classified_review import ClassifiedReview

router = APIRouter()


@router.get("/opportunities")
async def get_opportunities(db: AsyncSession = Depends(get_db)):
    """
    Get opportunity map data — each theme as a bubble:
    - X: frequency (review count)
    - Y: severity (avg negative sentiment score)
    - Size: cross-source consistency
    - Color: dominant segment
    """
    themes_query = select(Theme).order_by(Theme.review_count.desc())
    result = await db.execute(themes_query)
    themes = result.scalars().all()

    opportunities = []
    for theme in themes:
        # Calculate average severity (magnitude of negative sentiment)
        severity_query = (
            select(func.avg(func.abs(ClassifiedReview.sentiment_score)))
            .join(ReviewThemeMapping, ReviewThemeMapping.review_id == ClassifiedReview.id)
            .where(ReviewThemeMapping.theme_id == theme.id)
            .where(ClassifiedReview.sentiment_score < 0)
        )
        sev_result = await db.execute(severity_query)
        avg_severity = sev_result.scalar() or 0.0

        # Find dominant segment
        segment_query = (
            select(
                ClassifiedReview.user_segment_signal,
                func.count().label("cnt")
            )
            .join(ReviewThemeMapping, ReviewThemeMapping.review_id == ClassifiedReview.id)
            .where(ReviewThemeMapping.theme_id == theme.id)
            .where(ClassifiedReview.user_segment_signal.isnot(None))
            .group_by(ClassifiedReview.user_segment_signal)
            .order_by(func.count().desc())
            .limit(1)
        )
        seg_result = await db.execute(segment_query)
        dominant_segment = seg_result.first()

        opportunities.append({
            "theme_id": str(theme.id),
            "theme_name": theme.theme_name,
            "frequency": theme.review_count or 0,
            "severity": round(avg_severity, 3),
            "cross_source_score": theme.cross_source_count or 0,
            "dominant_segment": dominant_segment[0] if dominant_segment else "unclear",
            "confidence_level": theme.confidence_level,
            "trend_direction": theme.trend_direction,
            "representative_quote": theme.representative_quote,
        })

    return {"opportunities": opportunities, "total": len(opportunities)}
