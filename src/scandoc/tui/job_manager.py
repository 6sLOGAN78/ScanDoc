"""
Application Layer Job Manager for background worker tasks and job status tracking.
"""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from scandoc.tui.events import AppEvent, EventType, default_event_bus


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class Job:
    job_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    document_path: Optional[Path] = None
    task_name: str = "Document Pipeline"
    status: JobStatus = JobStatus.QUEUED
    progress_pct: float = 0.0
    current_stage: str = "Pending"
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result_data: Optional[Any] = None


class JobManager:
    """
    Centralized Job Manager handling async background processing, task queues,
    cancellation tokens, and progress notifications.
    """

    def __init__(self, max_workers: int = 4):
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self.jobs: Dict[str, Job] = {}

    def create_job(self, document_path: Path, task_name: str = "Document Pipeline") -> Job:
        job = Job(document_path=document_path, task_name=task_name)
        self.jobs[job.job_id] = job
        default_event_bus.publish(
            AppEvent(
                event_type=EventType.JOB_STATUS_CHANGED,
                payload={"job_id": job.job_id, "status": job.status},
                message=f"Job '{job.job_id}' queued for '{document_path.name}'",
            )
        )
        return job

    def list_jobs(self) -> List[Job]:
        return sorted(self.jobs.values(), key=lambda j: j.started_at or datetime.max, reverse=True)

    def get_job(self, job_id: str) -> Optional[Job]:
        return self.jobs.get(job_id)

    def cancel_job(self, job_id: str) -> bool:
        job = self.jobs.get(job_id)
        if job and job.status in (JobStatus.QUEUED, JobStatus.RUNNING):
            job.status = JobStatus.CANCELLED
            job.finished_at = datetime.now()
            default_event_bus.publish(
                AppEvent(
                    event_type=EventType.JOB_STATUS_CHANGED,
                    payload={"job_id": job_id, "status": JobStatus.CANCELLED},
                    message=f"Job '{job_id}' cancelled.",
                )
            )
            return True
        return False


default_job_manager = JobManager()
