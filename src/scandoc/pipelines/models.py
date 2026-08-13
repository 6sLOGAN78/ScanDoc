"""
Pydantic data models for pipeline configuration, performance metrics, and results.
"""

from typing import List, Optional, Union
from pydantic import BaseModel, Field

from scandoc.models import DocumentIR
from scandoc.pipelines.taxonomy import OrderingMode


class PipelineConfig(BaseModel):
    """
    Configuration parameters for multi-worker document pipeline execution.
    """
    max_workers: int = Field(4, ge=1, le=64, description="Worker thread pool concurrency limit")
    batch_size: int = Field(4, ge=1, le=128, description="Optimal document batch size")
    queue_size: int = Field(16, ge=1, le=512, description="Bounded queue capacity for backpressure control")
    ordering_mode: OrderingMode = Field(OrderingMode.ORDERED, description="Stream output ordering mode")
    chunk_size: int = Field(10, ge=1, description="Page chunking threshold for large document memory bounding")
    max_retries: int = Field(2, ge=0, description="Max retries for transient worker failures")
    timeout_seconds: float = Field(60.0, ge=0.1, description="Timeout limit per document processing task")
    export_format: Optional[str] = Field(None, description="Optional target exporter format (markdown, html, json, text, docx)")


class PipelineMetrics(BaseModel):
    """
    Performance and operational metrics collected during pipeline execution.
    """
    documents_processed: int = Field(0, ge=0, description="Total documents processed")
    pages_processed: int = Field(0, ge=0, description="Total pages processed")
    successful_pages: int = Field(0, ge=0, description="Number of successfully processed pages")
    failed_pages: int = Field(0, ge=0, description="Number of failed pages")
    total_processing_time_ms: float = Field(0.0, ge=0.0, description="Total processing wall-clock time in milliseconds")
    average_page_latency_ms: float = Field(0.0, ge=0.0, description="Average latency per page in milliseconds")
    pages_per_second: float = Field(0.0, ge=0.0, description="Throughput in pages per second")


class PipelineResult(BaseModel):
    """
    Outcome container for a processed document task.
    """
    document_id: str = Field(..., description="Document identifier")
    document_ir: Optional[DocumentIR] = Field(None, description="Extracted DocumentIR instance")
    status: str = Field("success", description="Processing status ('success', 'failed', 'cancelled')")
    errors: List[str] = Field(default_factory=list, description="List of non-fatal warnings or fatal errors")
    metrics: PipelineMetrics = Field(default_factory=PipelineMetrics, description="Execution performance metrics")
    exported_content: Optional[Union[str, bytes]] = Field(None, description="Optional rendered export string or bytes")
