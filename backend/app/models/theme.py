"""
Theme and ReviewThemeMapping models — stores clustered themes and review-to-theme links.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Text, DateTime, Float, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Theme(Base):
    __tablename__ = "themes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cluster_id = Column(Integer, unique=True, nullable=False, index=True)
    theme_name = Column(String(255), nullable=False)
    theme_description = Column(Text, nullable=True)
    representative_quote = Column(Text, nullable=True)
    review_count = Column(Integer, default=0)
    cross_source_count = Column(Integer, default=0)  # how many distinct sources mention this theme
    confidence_level = Column(String(20), nullable=True)  # 'high', 'medium', 'low'
    trend_direction = Column(String(20), nullable=True)  # 'growing', 'stable', 'declining'
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    review_mappings = relationship("ReviewThemeMapping", back_populates="theme", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Theme(id={self.id}, name='{self.theme_name}', reviews={self.review_count})>"


class ReviewThemeMapping(Base):
    __tablename__ = "review_theme_mapping"

    review_id = Column(UUID(as_uuid=True), ForeignKey("classified_reviews.id"), primary_key=True)
    theme_id = Column(UUID(as_uuid=True), ForeignKey("themes.id"), primary_key=True)
    similarity_score = Column(Float, nullable=True)

    # Relationships
    classified_review = relationship("ClassifiedReview", back_populates="theme_mappings")
    theme = relationship("Theme", back_populates="review_mappings")

    def __repr__(self):
        return f"<ReviewThemeMapping(review={self.review_id}, theme={self.theme_id}, score={self.similarity_score})>"
