"""
Monitoring Service — health checks, alerting, and pipeline run tracking.
Implements spec §9.2 monitoring requirements.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from app.models.pipeline_run import PipelineRun
from app.models.classified_review import ClassifiedReview
from app.models.raw_review import RawReview

logger = logging.getLogger(__name__)


class MonitoringService:
    """Monitors pipeline health and triggers alerts on failure conditions."""

    # Alert thresholds (from spec §9.2)
    MAX_CLASSIFICATION_FAILURE_RATE = 0.05  # 5%
    MAX_DASHBOARD_RESPONSE_MS = 3000  # 3 seconds
    ZERO_INGESTION_ALERT = True

    def __init__(self, db: AsyncSession):
        self.db = db
        self.alerts: list = []

    async def run_health_check(self) -> Dict[str, Any]:
        """Run all health checks and send alerts if thresholds are breached."""
        health = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "healthy",
            "checks": {},
            "alerts": [],
        }

        # Check 1: Last ingestion returned entries
        ingestion_check = await self._check_last_ingestion()
        health["checks"]["last_ingestion"] = ingestion_check
        if ingestion_check.get("alert"):
            health["alerts"].append(ingestion_check["alert"])
            health["status"] = "degraded"

        # Check 2: Classification failure rate
        failure_check = await self._check_classification_failure_rate()
        health["checks"]["classification_failure_rate"] = failure_check
        if failure_check.get("alert"):
            health["alerts"].append(failure_check["alert"])
            health["status"] = "degraded"

        # Check 3: Database connectivity
        db_check = await self._check_database()
        health["checks"]["database"] = db_check
        if not db_check.get("ok"):
            health["status"] = "unhealthy"

        # Check 4: Data freshness (last ingestion < 8 days ago)
        freshness_check = await self._check_data_freshness()
        health["checks"]["data_freshness"] = freshness_check
        if freshness_check.get("alert"):
            health["alerts"].append(freshness_check["alert"])

        # Send alerts
        if health["alerts"]:
            await self._send_alerts(health["alerts"])
            logger.warning(f"[monitor] {len(health['alerts'])} alert(s) triggered: {health['alerts']}")

        # Log health check to pipeline_runs
        run = PipelineRun(
            job_name="health_check",
            status="completed",
            completed_at=datetime.now(timezone.utc),
            duration_seconds=0,
            details=health,
        )
        self.db.add(run)

        return health

    async def _check_last_ingestion(self) -> Dict[str, Any]:
        """Check if the last ingestion job returned any entries."""
        result = await self.db.execute(
            select(PipelineRun)
            .where(PipelineRun.job_name == "ingest_all_sources")
            .order_by(PipelineRun.started_at.desc())
            .limit(1)
        )
        last_run = result.scalar_one_or_none()

        if not last_run:
            return {"status": "no_runs", "ok": True}

        if last_run.entries_processed == 0:
            return {
                "status": "zero_entries",
                "ok": False,
                "last_run": last_run.started_at.isoformat(),
                "alert": "⚠️ Last ingestion returned 0 entries — possible scraper failure",
            }

        return {
            "status": "ok",
            "ok": True,
            "entries_last_run": last_run.entries_processed,
            "last_run": last_run.started_at.isoformat(),
        }

    async def _check_classification_failure_rate(self) -> Dict[str, Any]:
        """Check if classification failure rate exceeds 5%."""
        total_result = await self.db.execute(
            select(func.count()).select_from(ClassifiedReview)
        )
        total = total_result.scalar() or 0

        failed_result = await self.db.execute(
            select(func.count())
            .select_from(ClassifiedReview)
            .where(ClassifiedReview.classification_failed == True)
        )
        failed = failed_result.scalar() or 0

        if total == 0:
            return {"status": "no_data", "ok": True}

        failure_rate = failed / total
        ok = failure_rate <= self.MAX_CLASSIFICATION_FAILURE_RATE

        return {
            "status": "ok" if ok else "threshold_exceeded",
            "ok": ok,
            "failure_rate": round(failure_rate * 100, 2),
            "total": total,
            "failed": failed,
            "alert": (
                f"⚠️ Classification failure rate is {failure_rate*100:.1f}% (threshold: 5%)"
                if not ok else None
            ),
        }

    async def _check_database(self) -> Dict[str, Any]:
        """Verify database connectivity."""
        try:
            await self.db.execute(text("SELECT 1"))
            return {"status": "connected", "ok": True}
        except Exception as e:
            return {"status": "error", "ok": False, "message": str(e)}

    async def _check_data_freshness(self) -> Dict[str, Any]:
        """Check that data was ingested within the last 8 days."""
        result = await self.db.execute(
            select(func.max(RawReview.ingested_at))
        )
        last_ingested = result.scalar()

        if not last_ingested:
            return {"status": "no_data", "ok": True}

        days_since = (datetime.now(timezone.utc) - last_ingested).days

        if days_since > 8:
            return {
                "status": "stale",
                "ok": False,
                "days_since_ingestion": days_since,
                "alert": f"⚠️ Data is {days_since} days old — weekly ingestion may have failed",
            }

        return {
            "status": "fresh",
            "ok": True,
            "days_since_ingestion": days_since,
        }

    async def _send_alerts(self, alerts: list):
        """Send alerts via configured channel (Slack webhook or email)."""
        from app.config import settings

        # Log alerts regardless
        for alert in alerts:
            logger.warning(f"ALERT: {alert}")

        # TODO: Integrate Slack webhook or email via settings.slack_webhook_url
        # async with httpx.AsyncClient() as client:
        #     await client.post(settings.slack_webhook_url, json={"text": "\n".join(alerts)})

    async def start_pipeline_run(self, job_name: str) -> PipelineRun:
        """Record the start of a pipeline job."""
        run = PipelineRun(job_name=job_name, status="running")
        self.db.add(run)
        await self.db.flush()
        return run

    async def complete_pipeline_run(
        self,
        run: PipelineRun,
        status: str = "completed",
        entries_processed: int = 0,
        entries_created: int = 0,
        entries_failed: int = 0,
        error: Optional[str] = None,
    ):
        """Record the completion of a pipeline job."""
        run.status = status
        run.completed_at = datetime.now(timezone.utc)
        run.entries_processed = entries_processed
        run.entries_created = entries_created
        run.entries_failed = entries_failed
        run.error_message = error

        if run.started_at:
            run.duration_seconds = (run.completed_at - run.started_at).total_seconds()
