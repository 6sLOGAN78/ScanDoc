"""
Data models for format detection and provider registry information.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class FormatDetectionResult(BaseModel):
    """
    Structured outcome of document format detection.
    """
    detected_format: str = Field(
        ...,
        description="Normalized format identifier (e.g. 'pdf', 'docx', 'pptx', 'html', 'image', 'txt', 'markdown')"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Detection confidence score (0.0 to 1.0)"
    )
    mime_type: str = Field(..., description="Detected MIME type (e.g. 'application/pdf')")
    extension: str = Field(..., description="Associated file extension with dot (e.g. '.pdf')")
    detection_method: str = Field(
        ...,
        description="Method used for detection ('explicit_override', 'magic_bytes', 'extension', 'content_heuristics')"
    )


class ProviderInfo(BaseModel):
    """
    Metadata describing a registered format provider's capabilities.
    """
    name: str = Field(..., description="Unique provider format name")
    supported_extensions: List[str] = Field(default_factory=list, description="Supported file extensions")
    supported_mime_types: List[str] = Field(default_factory=list, description="Supported MIME types")
    is_fully_implemented: bool = Field(
        False,
        description="True if full extraction is implemented, False if placeholder/stub"
    )
    description: str = Field("", description="Short provider description")
