"""
Segments endpoints — user segment summaries and deep-dive breakdowns.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.classified_review import ClassifiedReview
from app.models.raw_review import RawReview

router = APIRouter()

VALID_SEGMENTS = [
    "active_explorer_stuck",
    "background_listener",
    "mood_regulator",
    "identity_listener",
    "socially_led_discoverer",
    "new_user",
    "unclear",
]


@router.get("/segments")
async def list_segments(db: AsyncSession = Depends(get_db)):
    """Get summary stats for all user segments."""
    segments = []

    for segment_name in VALID_SEGMENTS:
        # Count reviews in this segment
        count_query = (
            select(func.count())
            .select_from(ClassifiedReview)
            .where(ClassifiedReview.user_segment_signal == segment_name)
            .where(ClassifiedReview.classification_failed == False)
        )
        result = await db.execute(count_query)
        count = result.scalar()

        if count > 0:
            # Get top complaint category
            category_query = (
                select(
                    ClassifiedReview.primary_complaint_category,
                    func.count().label("cnt")
                )
                .where(ClassifiedReview.user_segment_signal == segment_name)
                .where(ClassifiedReview.primary_complaint_category.isnot(None))
                .group_by(ClassifiedReview.primary_complaint_category)
                .order_by(func.count().desc())
                .limit(1)
            )
            cat_result = await db.execute(category_query)
            top_cat = cat_result.first()

            segments.append({
                "segment": segment_name,
                "review_count": count,
                "top_complaint": top_cat[0] if top_cat else None,
            })

    return {"segments": segments, "total_segments": len(segments)}


@router.get("/segments/{segment_id}")
async def get_segment(segment_id: str, db: AsyncSession = Depends(get_db)):
    """Deep-dive into a specific user segment — complaints, needs, sentiment, JTBD, quotes."""
    if segment_id not in VALID_SEGMENTS:
        raise HTTPException(status_code=404, detail=f"Invalid segment '{segment_id}'")

    # Get all classified reviews for this segment
    query = (
        select(ClassifiedReview, RawReview)
        .join(RawReview, ClassifiedReview.raw_review_id == RawReview.id)
        .where(ClassifiedReview.user_segment_signal == segment_id)
        .where(ClassifiedReview.classification_failed == False)
    )
    result = await db.execute(query)
    rows = result.all()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No reviews found for segment '{segment_id}'")

    # Aggregate data
    complaint_counts = {}
    unmet_needs = {}
    sentiment_counts = {}
    source_counts = {}
    jtbd_statements = []
    quotes = []

    for classified, raw in rows:
        # Top complaint categories
        cat = classified.primary_complaint_category
        if cat:
            complaint_counts[cat] = complaint_counts.get(cat, 0) + 1

        # Unmet needs
        need = classified.unmet_need
        if need:
            unmet_needs[need] = unmet_needs.get(need, 0) + 1

        # Sentiment distribution
        sent = classified.sentiment or "neutral"
        sentiment_counts[sent] = sentiment_counts.get(sent, 0) + 1

        # Cross-source presence
        source_counts[raw.source] = source_counts.get(raw.source, 0) + 1

        # JTBD statements (top 5)
        if classified.jtbd_statement and len(jtbd_statements) < 5:
            jtbd_statements.append(classified.jtbd_statement)

        # Representative quotes (top 10)
        if classified.key_frustration_phrase and len(quotes) < 10:
            quotes.append({
                "quote": classified.key_frustration_phrase,
                "source": raw.source,
                "date": raw.published_at.isoformat() if raw.published_at else None,
                "rating": raw.rating,
                "sentiment": classified.sentiment,
            })

    # Sort and limit complaints and needs
    top_complaints = sorted(complaint_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    top_needs = sorted(unmet_needs.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "segment": segment_id,
        "total_reviews": len(rows),
        "top_complaints": [{"category": c, "count": n} for c, n in top_complaints],
        "top_unmet_needs": [{"need": n, "count": c} for n, c in top_needs],
        "sentiment_distribution": sentiment_counts,
        "cross_source_presence": source_counts,
        "jtbd_statements": jtbd_statements,
        "representative_quotes": quotes,
    }
