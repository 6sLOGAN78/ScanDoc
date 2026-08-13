"""
Pydantic data models for OCR configuration, text region, and OCR result.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from scandoc.models.geometry import BoundingBox, Point2D


class OcrConfig(BaseModel):
    """
    Provider-independent OCR configuration.
    """
    languages: List[str] = Field(default_factory=lambda: ["en"], description="Target language codes")
    use_gpu: bool = Field(False, description="True to enable GPU execution if supported")
    confidence_threshold: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score threshold for filtering text regions"
    )
    batch_size: int = Field(1, ge=1, description="Batch size for batch inference")
    extra_options: Dict[str, str] = Field(default_factory=dict, description="Provider-specific configuration key-values")


class OCRTextRegion(BaseModel):
    """
    Individual text region detected and recognized by an OCR provider.
    """
    text: str = Field(..., description="Recognized text content")
    bbox: BoundingBox = Field(..., description="Page-normalized bounding box [left, top, right, bottom]")
    polygon: Optional[List[Point2D]] = Field(None, description="Optional bounding polygon points")
    confidence: float = Field(..., ge=0.0, le=1.0, description="OCR recognition confidence (0.0 to 1.0)")
    region_idx: int = Field(0, ge=0, description="0-indexed detection order sequence")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Provider-specific region metadata")

    @field_validator("confidence")
    @classmethod
    def validate_confidence_bounds(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError(f"OCR region confidence ({v}) must be between 0.0 and 1.0")
        return round(v, 4)


class OCRResult(BaseModel):
    """
    Structured outcome of an OCR engine execution over an image.
    """
    full_text: str = Field("", description="Concatenated recognized text from all regions")
    regions: List[OCRTextRegion] = Field(default_factory=list, description="List of recognized text regions")
    provider_id: str = Field(..., description="Identifier of OCR provider (e.g. 'rapidocr', 'tesseract')")
    model_id: str = Field(..., description="Model identifier or checkpoint name (e.g. 'PP-OCRv4')")
    image_width: int = Field(..., ge=1, description="Pixel width of target input image")
    image_height: int = Field(..., ge=1, description="Pixel height of target input image")
    processing_time_ms: float = Field(0.0, ge=0.0, description="Inference latency in milliseconds")
    page_reference: Optional[int] = Field(None, ge=0, description="Associated document page index if known")
