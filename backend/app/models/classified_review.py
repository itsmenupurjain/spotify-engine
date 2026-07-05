"""
ClassifiedReview model — stores AI classification results with pgvector embeddings.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Text, Boolean, DateTime, Float, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.database import Base


class ClassifiedReview(Base):
    __tablename__ = "classified_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    raw_review_id = Column(UUID(as_uuid=True), ForeignKey("raw_reviews.id"), nullable=False, unique=True, index=True)

    # AI Classification fields (from spec §4.1)
    is_discovery_relevant = Column(Boolean, nullable=True)
    primary_complaint_category = Column(String(100), nullable=True, index=True)
    secondary_complaint_category = Column(String(100), nullable=True)
    user_segment_signal = Column(String(100), nullable=True, index=True)
    sentiment = Column(String(50), nullable=True, index=True)
    sentiment_score = Column(Float, nullable=True)
    discovery_intent = Column(String(20), nullable=True)
    repetition_behavior_mentioned = Column(Boolean, nullable=True)
    key_frustration_phrase = Column(Text, nullable=True)
    unmet_need = Column(Text, nullable=True)
    jtbd_statement = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    detected_language = Column(String(10), nullable=True)

    # Enrichment scores (computed during pipeline)
    source_weight = Column(Float, nullable=True)
    recency_score = Column(Float, nullable=True)

    # Embedding vector (1536 dims for text-embedding-3-small)
    embedding = Column(Vector(1536), nullable=True)

    # Processing metadata
    classified_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    classification_model = Column(String(50), nullable=True)
    classification_failed = Column(Boolean, default=False)
    embedding_pending = Column(Boolean, default=True)

    # Relationships
    raw_review = relationship("RawReview", back_populates="classified_review")
    theme_mappings = relationship("ReviewThemeMapping", back_populates="classified_review", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ClassifiedReview(id={self.id}, category='{self.primary_complaint_category}', segment='{self.user_segment_signal}')>"
