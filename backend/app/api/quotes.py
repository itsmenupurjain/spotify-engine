"""
Quotes and Collections endpoints — filtered quotes and PM's saved quote collections.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from app.database import get_db
from app.models.classified_review import ClassifiedReview
from app.models.raw_review import RawReview
from app.models.collection import QuoteCollection, CollectionItem

router = APIRouter()


# --- Quotes ---

@router.get("/quotes")
async def list_quotes(
    source: Optional[str] = Query(None),
    segment: Optional[str] = Query(None),
    theme_id: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    min_rating: Optional[int] = Query(None, ge=1, le=5),
    max_rating: Optional[int] = Query(None, ge=1, le=5),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get filtered quotes for the Quote Library view."""
    query = (
        select(ClassifiedReview, RawReview)
        .join(RawReview, ClassifiedReview.raw_review_id == RawReview.id)
        .where(ClassifiedReview.classification_failed == False)
        .where(ClassifiedReview.key_frustration_phrase.isnot(None))
    )

    if source:
        query = query.where(RawReview.source == source)
    if segment:
        query = query.where(ClassifiedReview.user_segment_signal == segment)
    if sentiment:
        query = query.where(ClassifiedReview.sentiment == sentiment)
    if date_from:
        query = query.where(RawReview.published_at >= date_from)
    if date_to:
        query = query.where(RawReview.published_at <= date_to)
    if min_rating:
        query = query.where(RawReview.rating >= min_rating)
    if max_rating:
        query = query.where(RawReview.rating <= max_rating)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Paginate
    query = query.order_by(RawReview.published_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)

    quotes = []
    for classified, raw in result.all():
        quotes.append({
            "id": str(classified.id),
            "key_frustration_phrase": classified.key_frustration_phrase,
            "full_body": raw.body,
            "source": raw.source,
            "published_at": raw.published_at.isoformat() if raw.published_at else None,
            "rating": raw.rating,
            "sentiment": classified.sentiment,
            "segment": classified.user_segment_signal,
            "unmet_need": classified.unmet_need,
            "primary_complaint_category": classified.primary_complaint_category,
        })

    return {
        "quotes": quotes,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# --- Collections ---

class CreateCollectionRequest(BaseModel):
    name: str
    description: Optional[str] = None


class AddToCollectionRequest(BaseModel):
    review_ids: List[str]
    note: Optional[str] = None


@router.get("/collections")
async def list_collections(db: AsyncSession = Depends(get_db)):
    """List all quote collections."""
    query = select(QuoteCollection).order_by(QuoteCollection.updated_at.desc())
    result = await db.execute(query)
    collections = result.scalars().all()

    return {
        "collections": [
            {
                "id": str(c.id),
                "name": c.name,
                "description": c.description,
                "item_count": len(c.items) if c.items else 0,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            }
            for c in collections
        ]
    }


@router.post("/collections")
async def create_collection(
    request: CreateCollectionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new quote collection."""
    collection = QuoteCollection(
        name=request.name,
        description=request.description,
    )
    db.add(collection)
    await db.flush()

    return {
        "id": str(collection.id),
        "name": collection.name,
        "description": collection.description,
    }


@router.put("/collections/{collection_id}")
async def update_collection(
    collection_id: UUID,
    request: AddToCollectionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Add quotes (classified review IDs) to a collection."""
    collection = await db.get(QuoteCollection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    added = 0
    for review_id_str in request.review_ids:
        review_id = UUID(review_id_str)
        # Check if already in collection
        existing = await db.execute(
            select(CollectionItem)
            .where(CollectionItem.collection_id == collection_id)
            .where(CollectionItem.classified_review_id == review_id)
        )
        if not existing.scalar_one_or_none():
            item = CollectionItem(
                collection_id=collection_id,
                classified_review_id=review_id,
                note=request.note,
            )
            db.add(item)
            added += 1

    return {"message": f"Added {added} quotes to collection '{collection.name}'"}
