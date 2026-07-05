"""
Reviews endpoints — list/filter reviews and get individual review details.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.database import get_db
from app.models.raw_review import RawReview
from app.models.classified_review import ClassifiedReview

router = APIRouter()


@router.get("/reviews")
async def list_reviews(
    source: Optional[str] = Query(None, description="Filter by source"),
    segment: Optional[str] = Query(None, description="Filter by user segment"),
    theme_id: Optional[str] = Query(None, description="Filter by theme ID"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment"),
    category: Optional[str] = Query(None, description="Filter by complaint category"),
    discovery_intent: Optional[str] = Query(None, description="Filter by discovery intent"),
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    min_rating: Optional[int] = Query(None, ge=1, le=5, description="Minimum rating"),
    max_rating: Optional[int] = Query(None, ge=1, le=5, description="Maximum rating"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """List reviews with comprehensive filtering, joining raw and classified data."""
    query = (
        select(ClassifiedReview, RawReview)
        .join(RawReview, ClassifiedReview.raw_review_id == RawReview.id)
        .where(ClassifiedReview.classification_failed == False)
    )

    # Apply filters
    if source:
        query = query.where(RawReview.source == source)
    if segment:
        query = query.where(ClassifiedReview.user_segment_signal == segment)
    if sentiment:
        query = query.where(ClassifiedReview.sentiment == sentiment)
    if category:
        query = query.where(ClassifiedReview.primary_complaint_category == category)
    if discovery_intent:
        query = query.where(ClassifiedReview.discovery_intent == discovery_intent)
    if date_from:
        query = query.where(RawReview.published_at >= date_from)
    if date_to:
        query = query.where(RawReview.published_at <= date_to)
    if min_rating:
        query = query.where(RawReview.rating >= min_rating)
    if max_rating:
        query = query.where(RawReview.rating <= max_rating)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Paginate
    query = query.order_by(RawReview.published_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    rows = result.all()

    reviews = []
    for classified, raw in rows:
        reviews.append({
            "id": str(classified.id),
            "raw_review_id": str(raw.id),
            "source": raw.source,
            "rating": raw.rating,
            "title": raw.title,
            "body": raw.body,
            "published_at": raw.published_at.isoformat() if raw.published_at else None,
            "engagement_score": raw.engagement_score,
            "primary_complaint_category": classified.primary_complaint_category,
            "secondary_complaint_category": classified.secondary_complaint_category,
            "user_segment_signal": classified.user_segment_signal,
            "sentiment": classified.sentiment,
            "sentiment_score": classified.sentiment_score,
            "discovery_intent": classified.discovery_intent,
            "repetition_behavior_mentioned": classified.repetition_behavior_mentioned,
            "key_frustration_phrase": classified.key_frustration_phrase,
            "unmet_need": classified.unmet_need,
            "jtbd_statement": classified.jtbd_statement,
            "confidence_score": classified.confidence_score,
        })

    return {
        "reviews": reviews,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total else 0,
    }


@router.get("/reviews/{review_id}")
async def get_review(review_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a single review with full classification details."""
    query = (
        select(ClassifiedReview, RawReview)
        .join(RawReview, ClassifiedReview.raw_review_id == RawReview.id)
        .where(ClassifiedReview.id == review_id)
    )
    result = await db.execute(query)
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Review not found")

    classified, raw = row
    return {
        "id": str(classified.id),
        "raw_review_id": str(raw.id),
        "source": raw.source,
        "external_id": raw.external_id,
        "rating": raw.rating,
        "title": raw.title,
        "body": raw.body,
        "author_hash": raw.author_hash,
        "published_at": raw.published_at.isoformat() if raw.published_at else None,
        "app_version": raw.app_version,
        "country_code": raw.country_code,
        "engagement_score": raw.engagement_score,
        "raw_url": raw.raw_url,
        "subreddit": raw.subreddit,
        "primary_complaint_category": classified.primary_complaint_category,
        "secondary_complaint_category": classified.secondary_complaint_category,
        "user_segment_signal": classified.user_segment_signal,
        "sentiment": classified.sentiment,
        "sentiment_score": classified.sentiment_score,
        "discovery_intent": classified.discovery_intent,
        "repetition_behavior_mentioned": classified.repetition_behavior_mentioned,
        "key_frustration_phrase": classified.key_frustration_phrase,
        "unmet_need": classified.unmet_need,
        "jtbd_statement": classified.jtbd_statement,
        "confidence_score": classified.confidence_score,
        "classification_model": classified.classification_model,
        "classified_at": classified.classified_at.isoformat() if classified.classified_at else None,
        "source_weight": classified.source_weight,
        "recency_score": classified.recency_score,
    }
