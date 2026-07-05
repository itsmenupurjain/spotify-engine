"""
QuoteCollection and CollectionItem models — PM's saved quote collections for decks.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class QuoteCollection(Base):
    __tablename__ = "quote_collections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    items = relationship("CollectionItem", back_populates="collection", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<QuoteCollection(name='{self.name}', items={len(self.items) if self.items else 0})>"


class CollectionItem(Base):
    __tablename__ = "collection_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collection_id = Column(UUID(as_uuid=True), ForeignKey("quote_collections.id"), nullable=False, index=True)
    classified_review_id = Column(UUID(as_uuid=True), ForeignKey("classified_reviews.id"), nullable=False, index=True)
    note = Column(Text, nullable=True)  # PM's annotation
    added_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    collection = relationship("QuoteCollection", back_populates="items")

    def __repr__(self):
        return f"<CollectionItem(collection={self.collection_id}, review={self.classified_review_id})>"
