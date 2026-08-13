"""
Exception classes for High-Performance Pipelines, Batching & Streaming Processing.
"""


class PipelineError(Exception):
    """Base exception for all document pipeline execution errors."""
    pass


class PipelineTimeoutError(PipelineError):
    """Raised when document or page processing exceeds the configured timeout."""
    pass


class PipelineCancelledError(PipelineError):
    """Raised when pipeline execution is cancelled by the caller."""
    pass


class WorkerExecutionError(PipelineError):
    """Raised when a background worker thread or task fails permanently."""
    pass


class QueueOverflowError(PipelineError):
    """Raised when bounded queue size is exceeded under extreme backpressure."""
    pass
