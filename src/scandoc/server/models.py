"""
Pydantic API request/response schemas for scanDOC REST API server.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from scandoc.server.taxonomy import JobStatus, ServerErrorCode, WebhookEventType


class ConvertRequest(BaseModel):
    """Configuration options for document conversion."""
    format: str = Field("markdown", description="Target output format: markdown, html, json, text, docx")
    device: Optional[str] = Field(None, description="Hardware device override (cpu, cuda, etc.)")
    provider: Optional[str] = Field(None, description="OCR/VLM provider override")
    model: Optional[str] = Field(None, description="Model ID override")
    webhook_url: Optional[str] = Field(None, description="Optional webhook URL for job completion notification")


class JobResponse(BaseModel):
    """Response returned upon job creation."""
    job_id: str
    status: JobStatus
    created_at: str
    message: str = "Job successfully created and queued."


class JobProgress(BaseModel):
    """Progress metrics for an active job."""
    pages_processed: int = 0
    total_pages: int = 0
    percentage: float = 0.0
    current_stage: str = "queued"
    elapsed_sec: float = 0.0


class JobStatusResponse(BaseModel):
    """Detailed job status response."""
    job_id: str
    status: JobStatus
    file_name: str
    format: str
    progress: JobProgress
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None


class WebhookPayload(BaseModel):
    """Standardized webhook notification payload."""
    event_id: str
    event_type: WebhookEventType
    job_id: str
    status: JobStatus
    timestamp: str
    result_url: Optional[str] = None
    error_message: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standardized REST API error diagnostic response."""
    error_code: ServerErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None
