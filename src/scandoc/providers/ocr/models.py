"""
Pydantic data models for OCR configuration, capabilities, text region, and OCR result.
"""

from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field, field_validator

from scandoc.models.geometry import BoundingBox, Point2D
from scandoc.providers.ocr.secrets import SecretRef


class OcrCapability(BaseModel):
    """
    Metadata describing specific capabilities supported by an OCR provider.
    """
    provider_id: str = Field(..., description="Unique provider ID (e.g. 'rapidocr', 'tesseract', 'remote_http')")
    is_local: bool = Field(True, description="True if executes locally on host, False if remote API call")
    supports_cpu: bool = Field(True, description="True if supports CPU execution")
    supports_gpu: bool = Field(False, description="True if supports GPU execution")
    supports_batch: bool = Field(False, description="True if supports hardware batch inference")
    supports_confidence: bool = Field(True, description="True if provides recognition confidence scores")
    supports_polygons: bool = Field(False, description="True if provides multi-point polygon contours")
    supports_orientation: bool = Field(False, description="True if supports image orientation detection")
    supported_languages: List[str] = Field(default_factory=list, description="ISO language codes supported")
    max_image_size_px: Optional[Tuple[int, int]] = Field(None, description="Maximum image size tuple (width, height)")


class OcrProviderConfig(BaseModel):
    """
    Provider-independent OCR configuration model.
    """
    provider_name: str = Field("rapidocr", description="Target provider ID ('rapidocr', 'tesseract', 'remote_http', 'auto')")
    model_name: str = Field("PP-OCRv4", description="Model checkpoint name")
    language: str = Field("en", description="Target language code")
    device: str = Field("cpu", description="Execution device ('cpu', 'cuda')")
    endpoint: Optional[str] = Field(None, description="HTTP endpoint URL for remote providers")
    api_key_ref: Optional[SecretRef] = Field(None, description="Secure reference to API key secret")
    timeout_sec: float = Field(30.0, ge=0.1, description="Request/inference timeout in seconds")
    batch_size: int = Field(1, ge=1, description="Batch size")
    confidence_threshold: float = Field(0.0, ge=0.0, le=1.0, description="Minimum confidence filter threshold")
    extra_options: Dict[str, str] = Field(default_factory=dict, description="Provider-specific options")


# Backward-compatibility alias
OcrConfig = OcrProviderConfig


class OCRTextRegion(BaseModel):
    """
    Individual text region recognized by an OCR engine.
    """
    text: str = Field(..., description="Recognized text string")
    bbox: BoundingBox = Field(..., description="Page-normalized bounding box [left, top, right, bottom]")
    polygon: Optional[List[Point2D]] = Field(None, description="Optional polygon contour points")
    confidence: float = Field(..., ge=0.0, le=1.0, description="OCR confidence (0.0 to 1.0)")
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
