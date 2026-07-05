"""
Ingestion & Pipeline trigger endpoints — manually trigger data ingestion and pipeline jobs.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone

from app.database import get_db, AsyncSessionLocal

router = APIRouter()
logger = logging.getLogger(__name__)


class IngestRequest(BaseModel):
    source: Optional[str] = None  # None = all sources; or 'app_store', 'play_store', 'reddit', etc.


class IngestResponse(BaseModel):
    status: str
    message: str
    job_id: Optional[str] = None


class PipelineJobStatus(BaseModel):
    job_name: str
    last_run: Optional[str] = None
    status: str
    entries_processed: Optional[int] = None


VALID_SOURCES = ["app_store", "play_store", "reddit", "spotify_community", "twitter_x"]
VALID_JOBS = ["classify", "embed", "cluster", "synthesize", "ingest"]


# Background task functions

async def _run_ingestion(source: Optional[str] = None):
    """Run ingestion pipeline in background."""
    async with AsyncSessionLocal() as db:
        try:
            from app.pipeline.orchestrator import PipelineOrchestrator
            orchestrator = PipelineOrchestrator(db)
            result = await orchestrator.run(source=source)
            await db.commit()
            logger.info(f"Ingestion complete: {result}")
        except Exception as e:
            await db.rollback()
            logger.error(f"Ingestion failed: {e}")


async def _run_pipeline_job(job_name: str):
    """Run a specific pipeline job in background."""
    from app.scheduler import (
        job_classify_new_reviews,
        job_embed_new_reviews,
        job_update_clusters,
        job_refresh_synthesis_cache,
    )

    job_map = {
        "classify": job_classify_new_reviews,
        "embed": job_embed_new_reviews,
        "cluster": job_update_clusters,
        "synthesize": job_refresh_synthesis_cache,
    }

    job_fn = job_map.get(job_name)
    if job_fn:
        await job_fn()


@router.post("/ingest/trigger", response_model=IngestResponse)
async def trigger_ingestion(
    request: IngestRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger ingestion for one or all sources."""
    if request.source and request.source not in VALID_SOURCES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source '{request.source}'. Valid sources: {VALID_SOURCES}"
        )

    source_label = request.source or "all sources"
    background_tasks.add_task(_run_ingestion, request.source)

    return IngestResponse(
        status="accepted",
        message=f"Ingestion triggered for {source_label}. Processing in background.",
    )


@router.post("/pipeline/trigger/{job_id}")
async def trigger_pipeline_job(
    job_id: str,
    background_tasks: BackgroundTasks,
):
    """
    Manually trigger a specific pipeline job.

    Valid job IDs: classify, embed, cluster, synthesize, ingest
    """
    if job_id not in VALID_JOBS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid job '{job_id}'. Valid jobs: {VALID_JOBS}"
        )

    if job_id == "ingest":
        background_tasks.add_task(_run_ingestion, None)
    else:
        background_tasks.add_task(_run_pipeline_job, job_id)

    return {
        "status": "accepted",
        "message": f"Pipeline job '{job_id}' triggered. Processing in background.",
        "job_id": job_id,
        "triggered_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/pipeline/status")
async def get_pipeline_status(db: AsyncSession = Depends(get_db)):
    """Get the status of recent pipeline runs."""
    from sqlalchemy import select
    from app.models.pipeline_run import PipelineRun

    query = (
        select(PipelineRun)
        .order_by(PipelineRun.started_at.desc())
        .limit(20)
    )
    result = await db.execute(query)
    runs = result.scalars().all()

    return {
        "recent_runs": [
            {
                "id": str(r.id),
                "job_name": r.job_name,
                "status": r.status,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "duration_seconds": r.duration_seconds,
                "entries_processed": r.entries_processed,
                "entries_created": r.entries_created,
                "entries_failed": r.entries_failed,
                "error_message": r.error_message,
            }
            for r in runs
        ],
        "total_runs": len(runs),
    }


@router.post("/pipeline/seed")
async def load_seed_data(
    db: AsyncSession = Depends(get_db),
):
    """
    Generate and load synthetic seed data into the database.
    Useful for development when API keys are not available.
    """
    import sys
    import os

    # Add scripts directory to path
    scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "scripts")
    sys.path.insert(0, scripts_dir)

    try:
        from seed_data import generate_seed_data
        import json
        import tempfile

        # Generate seed data
        data = generate_seed_data(count=600)

        # Save to temp file and load
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(data, f, default=str)
            temp_path = f.name

        from app.pipeline.orchestrator import PipelineOrchestrator
        orchestrator = PipelineOrchestrator(db)
        result = await orchestrator.load_seed_data(temp_path)
        await db.commit()

        # Cleanup
        os.unlink(temp_path)

        return {
            "status": "success",
            "message": "Seed data loaded successfully",
            **result,
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Seed data loading failed: {e}")
        raise HTTPException(status_code=500, detail=f"Seed data loading failed: {str(e)}")
