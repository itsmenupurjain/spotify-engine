"""
PipelineRun model — tracks execution stats for each pipeline job.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_name = Column(String(100), nullable=False, index=True)  # e.g. 'ingest_app_store', 'classify_reviews'
    status = Column(String(20), nullable=False, default="running")  # running, completed, failed
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    entries_processed = Column(Integer, default=0)
    entries_created = Column(Integer, default=0)
    entries_failed = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    details = Column(JSONB, nullable=True)  # Additional metadata about the run

    def __repr__(self):
        return f"<PipelineRun(job='{self.job_name}', status='{self.status}', processed={self.entries_processed})>"
