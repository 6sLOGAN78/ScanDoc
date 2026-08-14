"""
Taxonomy enums for scanDOC REST API server and job management.
"""

from enum import Enum


class JobStatus(str, Enum):
    """Lifecycle status states for asynchronous processing jobs."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WebhookEventType(str, Enum):
    """Supported webhook event types."""
    JOB_COMPLETED = "job.completed"
    JOB_FAILED = "job.failed"
    JOB_CANCELLED = "job.cancelled"


class ServerErrorCode(str, Enum):
    """Standardized REST API error codes."""
    INVALID_REQUEST = "INVALID_REQUEST"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    RESOURCE_LIMIT = "RESOURCE_LIMIT"
    PROCESSING_ERROR = "PROCESSING_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
