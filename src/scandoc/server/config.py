"""
Configuration settings for scanDOC REST API server.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ServerConfig(BaseModel):
    """
    Configuration parameters for scanDOC REST API Server.
    """
    host: str = Field("127.0.0.1", description="Binding host IP address")
    port: int = Field(8000, description="Binding port number")
    workers: int = Field(4, description="Background worker concurrency threads")
    device: str = Field("auto", description="Execution hardware target (auto, cpu, cuda, openvino, tensorrt, mps)")
    max_upload_bytes: int = Field(52428800, description="Maximum allowed file upload size in bytes (default: 50MB)")
    job_retention_sec: int = Field(3600, description="Time to keep completed jobs in memory")
    cors_origins: List[str] = Field(default_factory=lambda: ["*"], description="Allowed CORS origins")
    webhook_secret: Optional[str] = Field(None, description="Secret key for HMAC-SHA256 webhook signatures")
    webhook_timeout_sec: float = Field(5.0, description="Timeout for webhook delivery requests")
    webhook_max_retries: int = Field(3, description="Maximum retry attempts for failed webhook delivery")
