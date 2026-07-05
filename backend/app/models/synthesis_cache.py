"""
SynthesisCache model — pre-aggregated data for dashboard performance.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class SynthesisCache(Base):
    __tablename__ = "synthesis_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cache_key = Column(String(255), unique=True, nullable=False, index=True)  # e.g. 'theme_frequency_by_source_2025_q2'
    data = Column(JSONB, nullable=False)
    generated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<SynthesisCache(key='{self.cache_key}', generated={self.generated_at})>"
