"""
Data models for ingestion options and asset references.
"""

from typing import Optional, Tuple
from pydantic import BaseModel, Field


class IngestionOptions(BaseModel):
    """
    Configuration options for document ingestion and normalization.
    """
    max_file_size_bytes: int = Field(100 * 1024 * 1024, ge=1, description="Maximum allowed file size in bytes (default 100MB)")
    preserve_assets: bool = Field(True, description="Extract and preserve embedded images and binary assets")
    extract_metadata: bool = Field(True, description="Extract document header and author metadata")
    fallback_encoding: str = Field("utf-8", description="Fallback text encoding for plain text ingestion")


class AssetRef(BaseModel):
    """
    Normalized embedded image or binary asset reference.
    """
    asset_id: str = Field(..., description="Unique asset identifier")
    source_location: str = Field(..., description="Source location path or element reference")
    mime_type: str = Field("image/png", description="MIME type of asset payload")
    dimensions: Optional[Tuple[int, int]] = Field(None, description="Asset dimensions (width, height) in pixels")
    storage_ref: Optional[str] = Field(None, description="Internal storage path or byte buffer reference")
