"""
High-Performance Pipelines, Batching & Streaming Processing Subsystem for scanDOC.
"""

from scandoc.pipelines.exceptions import (
    PipelineCancelledError,
    PipelineError,
    PipelineTimeoutError,
    QueueOverflowError,
    WorkerExecutionError,
)
from scandoc.pipelines.executor import PipelineThreadPool
from scandoc.pipelines.models import PipelineConfig, PipelineMetrics, PipelineResult
from scandoc.pipelines.pipeline import DocumentPipeline
from scandoc.pipelines.taxonomy import OrderingMode, PipelineStage

__all__ = [
    "DocumentPipeline",
    "PipelineConfig",
    "PipelineMetrics",
    "PipelineResult",
    "PipelineThreadPool",
    "OrderingMode",
    "PipelineStage",
    "PipelineError",
    "PipelineTimeoutError",
    "PipelineCancelledError",
    "WorkerExecutionError",
    "QueueOverflowError",
]
