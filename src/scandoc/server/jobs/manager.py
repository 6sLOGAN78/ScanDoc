"""
Async job manager handling background thread pool execution and lifecycle transitions.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import os
from pathlib import Path
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from scandoc.exporters import default_exporter_registry, ExportOptions
from scandoc.pipelines import DocumentPipeline, PipelineConfig, OrderingMode
from scandoc.server.config import ServerConfig
from scandoc.server.jobs.store import JobRecord, JobStore
from scandoc.server.models import JobProgress, JobStatusResponse, ConvertRequest
from scandoc.server.taxonomy import JobStatus
from scandoc.server.webhooks import WebhookDispatcher


class AsyncJobManager:
    """
    Orchestrates asynchronous job queueing, execution, cancellation, and metrics.
    """

    def __init__(self, config: ServerConfig):
        self.config = config
        self.store = JobStore()
        self.executor = ThreadPoolExecutor(max_workers=config.workers, thread_name_prefix="scandoc_job_worker")
        self.webhook_dispatcher = WebhookDispatcher(
            secret=config.webhook_secret,
            timeout_sec=config.webhook_timeout_sec,
            max_retries=config.webhook_max_retries,
        )
        self._telemetry = {
            "total_jobs": 0,
            "completed_jobs": 0,
            "failed_jobs": 0,
            "cancelled_jobs": 0,
        }

    def create_job(
        self,
        file_name: str,
        temp_path: Path,
        request: ConvertRequest,
    ) -> JobRecord:
        """Create and queue a new processing job."""
        job_id = str(uuid.uuid4())
        job = JobRecord(
            job_id=job_id,
            file_name=file_name,
            temp_file_path=temp_path,
            format=request.format.lower(),
            device=request.device or self.config.device,
            provider=request.provider,
            model=request.model,
            webhook_url=request.webhook_url,
            status=JobStatus.QUEUED,
        )
        self.store.add_job(job)
        self._telemetry["total_jobs"] += 1

        # Submit background processing to thread pool executor
        self.executor.submit(self._execute_job_thread, job_id)
        return job

    def get_job_status(self, job_id: str) -> Optional[JobStatusResponse]:
        """Query status response for job ID."""
        job = self.store.get_job(job_id)
        if not job:
            return None

        return JobStatusResponse(
            job_id=job.job_id,
            status=job.status,
            file_name=job.file_name,
            format=job.format,
            progress=job.progress,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            error_message=job.error_message,
        )

    def cancel_job(self, job_id: str) -> Tuple[bool, str]:
        """Request cancellation of queued or running job."""
        job = self.store.get_job(job_id)
        if not job:
            return False, f"Job '{job_id}' not found."

        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            return False, f"Job '{job_id}' is already in terminal state '{job.status.value}'."

        job.cancel_requested = True
        if job.status == JobStatus.QUEUED:
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            self._telemetry["cancelled_jobs"] += 1
            self._cleanup_file(job.temp_file_path)
            self._trigger_webhook(job)

        return True, f"Job '{job_id}' cancellation requested."

    def get_job_result(self, job_id: str, format_override: Optional[str] = None) -> Tuple[Optional[Any], Optional[str]]:
        """Retrieve exported content for completed job."""
        job = self.store.get_job(job_id)
        if not job:
            return None, f"Job '{job_id}' not found."

        if job.status != JobStatus.COMPLETED or not job.document_ir:
            return None, f"Job '{job_id}' is not completed. Current status: '{job.status.value}'."

        fmt = (format_override or job.format).lower()
        try:
            exp_res = default_exporter_registry.export(job.document_ir, ExportOptions(format_id=fmt))
            return exp_res.content, None
        except Exception as exc:
            return None, f"Failed to export format '{fmt}': {exc}"

    def get_telemetry(self) -> Dict[str, Any]:
        """Return server job telemetry metrics."""
        active_count = sum(1 for j in self.store.list_jobs() if j.status in [JobStatus.QUEUED, JobStatus.RUNNING])
        return {
            **self._telemetry,
            "active_jobs": active_count,
            "stored_jobs": len(self.store.list_jobs()),
        }

    def shutdown(self) -> None:
        """Gracefully shut down worker thread pool."""
        self.executor.shutdown(wait=False, cancel_futures=True)

    def _execute_job_thread(self, job_id: str) -> None:
        """Background thread execution worker logic."""
        job = self.store.get_job(job_id)
        if not job or job.cancel_requested:
            if job:
                job.status = JobStatus.CANCELLED
                self._cleanup_file(job.temp_file_path)
            return

        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        job.progress.current_stage = "processing"
        t0 = time.perf_counter()

        try:
            p_config = PipelineConfig(max_workers=1, ordering_mode=OrderingMode.ORDERED)
            pipeline = DocumentPipeline(config=p_config)

            if job.cancel_requested:
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                self._telemetry["cancelled_jobs"] += 1
                self._cleanup_file(job.temp_file_path)
                self._trigger_webhook(job)
                return

            p_result = pipeline.process(job.temp_file_path)
            elapsed = time.perf_counter() - t0

            if job.cancel_requested:
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                self._telemetry["cancelled_jobs"] += 1
                self._cleanup_file(job.temp_file_path)
                self._trigger_webhook(job)
                return

            if p_result.status != "success" or not p_result.document_ir:
                err_msg = "; ".join(p_result.errors) if p_result.errors else "Pipeline processing failed."
                job.status = JobStatus.FAILED
                job.error_message = err_msg
                job.completed_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                self._telemetry["failed_jobs"] += 1
            else:
                job.status = JobStatus.COMPLETED
                job.document_ir = p_result.document_ir
                job.completed_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                pages_cnt = len(p_result.document_ir.pages)
                job.progress = JobProgress(
                    pages_processed=pages_cnt,
                    total_pages=pages_cnt,
                    percentage=100.0,
                    current_stage="completed",
                    elapsed_sec=round(elapsed, 3),
                )
                self._telemetry["completed_jobs"] += 1

        except Exception as exc:
            job.status = JobStatus.FAILED
            job.error_message = str(exc)
            job.completed_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            self._telemetry["failed_jobs"] += 1
        finally:
            self._cleanup_file(job.temp_file_path)
            self._trigger_webhook(job)

    def _cleanup_file(self, path: Path) -> None:
        """Deterministically clean up temporary uploaded file."""
        try:
            if path.exists() and path.is_file():
                os.remove(path)
        except Exception:
            pass

    def _trigger_webhook(self, job: JobRecord) -> None:
        """Trigger async webhook delivery if webhook_url is set."""
        if not job.webhook_url:
            return

        result_url = f"/api/v1/jobs/{job.job_id}/result" if job.status == JobStatus.COMPLETED else None

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self.webhook_dispatcher.dispatch_job_event(
                        webhook_url=job.webhook_url,
                        job_id=job.job_id,
                        status=job.status,
                        result_url=result_url,
                        error_message=job.error_message,
                    ),
                    loop,
                )
            else:
                asyncio.run(
                    self.webhook_dispatcher.dispatch_job_event(
                        webhook_url=job.webhook_url,
                        job_id=job.job_id,
                        status=job.status,
                        result_url=result_url,
                        error_message=job.error_message,
                    )
                )
        except Exception:
            pass
