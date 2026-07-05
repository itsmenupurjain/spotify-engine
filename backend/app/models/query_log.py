"""
QueryLog model — tracks PM natural language queries for analytics.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from app.database import Base


class QueryLog(Base):
    __tablename__ = "query_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_text = Column(Text, nullable=False)
    query_embedding = Column(Vector(1536), nullable=True)
    result_count = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    queried_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<QueryLog(query='{self.query_text[:50]}...', results={self.result_count})>"
