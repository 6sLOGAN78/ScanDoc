"""
In-memory job storage for scanDOC REST API server.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import threading
from typing import Dict, List, Optional

from scandoc.models import DocumentIR
from scandoc.server.models import JobProgress
from scandoc.server.taxonomy import JobStatus


@dataclass
class JobRecord:
    """Internal job state record."""
    job_id: str
    file_name: str
    temp_file_path: Path
    format: str
    device: str
    provider: Optional[str]
    model: Optional[str]
    webhook_url: Optional[str]
    status: JobStatus = JobStatus.QUEUED
    progress: JobProgress = field(default_factory=JobProgress)
    created_at: str = field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    document_ir: Optional[DocumentIR] = None
    error_message: Optional[str] = None
    cancel_requested: bool = False


class JobStore:
    """Thread-safe in-memory job repository."""

    def __init__(self):
        self._jobs: Dict[str, JobRecord] = {}
        self._lock = threading.Lock()

    def add_job(self, job: JobRecord) -> None:
        with self._lock:
            self._jobs[job.job_id] = job

    def get_job(self, job_id: str) -> Optional[JobRecord]:
        with self._lock:
            return self._jobs.get(job_id)

    def list_jobs(self) -> List[JobRecord]:
        with self._lock:
            return list(self._jobs.values())

    def remove_job(self, job_id: str) -> bool:
        with self._lock:
            return self._jobs.pop(job_id, None) is not None
