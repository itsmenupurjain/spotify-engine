"""
RawReview model — stores ingested reviews from all 5 sources before AI classification.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Text, Boolean, DateTime, Float
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class RawReview(Base):
    __tablename__ = "raw_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(50), nullable=False, index=True)  # app_store, play_store, reddit, spotify_community, twitter_x
    external_id = Column(String(255), unique=True, index=True)
    rating = Column(Integer, nullable=True)  # NULL for sources without ratings
    title = Column(Text, nullable=True)
    body = Column(Text, nullable=False)
    author_hash = Column(String(64), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True, index=True)
    app_version = Column(String(50), nullable=True)
    country_code = Column(String(10), nullable=True)
    engagement_score = Column(Integer, nullable=True)  # helpful_votes / upvotes / likes
    raw_url = Column(Text, nullable=True)
    ingested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    language = Column(String(10), nullable=True)
    is_relevant = Column(Boolean, nullable=True)  # set after relevance filter
    exclusion_reason = Column(String(255), nullable=True)
    body_hash = Column(String(64), nullable=True, index=True)  # SHA-256 for dedup

    # Metadata enrichment
    source_weight = Column(Float, nullable=True)
    recency_score = Column(Float, nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # Extra fields for Reddit
    subreddit = Column(String(100), nullable=True)
    post_title = Column(Text, nullable=True)
    post_score = Column(Integer, nullable=True)
    comment_score = Column(Integer, nullable=True)
    is_comment = Column(Boolean, default=False)
    parent_post_id = Column(String(255), nullable=True)

    # Extra fields for Community Forums
    reply_count = Column(Integer, nullable=True)
    kudos_count = Column(Integer, nullable=True)
    thread_status = Column(String(100), nullable=True)  # 'Not Right Now', 'Under Consideration', etc.

    # Extra fields for Twitter
    like_count = Column(Integer, nullable=True)
    retweet_count = Column(Integer, nullable=True)

    # Relationship
    classified_review = relationship("ClassifiedReview", back_populates="raw_review", uselist=False)

    def __repr__(self):
        return f"<RawReview(id={self.id}, source='{self.source}', external_id='{self.external_id}')>"
