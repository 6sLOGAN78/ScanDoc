"""
Data models for figure configuration, ImageInput payload, and FigureResult.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from scandoc.models.geometry import BoundingBox, Point2D
from scandoc.models.provenance import Provenance
from scandoc.providers.ocr.secrets import SecretRef
from scandoc.providers.figures.taxonomy import FigureType, ProviderType


class FigureConfig(BaseModel):
    """
    Configuration model for figure and image understanding providers.
    """
    model_name: str = Field("BasicFigureAnalyzer", description="Target model or provider name")
    provider_type: ProviderType = Field(ProviderType.LOCAL, description="Provider execution type (LOCAL, HUGGINGFACE, REMOTE)")
    model_path: Optional[str] = Field(None, description="Path to local model weights")
    endpoint: Optional[str] = Field(None, description="HTTP endpoint for remote providers")
    api_key_ref: Optional[SecretRef] = Field(None, description="Secure reference to API key")
    device: str = Field("auto", description="Execution device ('cpu', 'cuda', 'auto')")
    allow_remote: bool = Field(False, description="Privacy flag: Must be True to invoke remote providers")
    extra_options: Dict[str, str] = Field(default_factory=dict, description="Provider-specific options")


class ImageInput(BaseModel):
    """
    Provider-independent input image payload container avoiding unnecessary image copies.
    """
    source_type: str = Field("raster", description="Origin category ('embedded', 'raster', 'layout_region')")
    image_bytes: Optional[bytes] = Field(None, description="Raw image bytes payload")
    image_path: Optional[str] = Field(None, description="Path to image file")
    page_index: int = Field(0, ge=0, description="Target document page index")
    bbox: Optional[BoundingBox] = Field(None, description="Normalized bounding box of image on page")
    width: Optional[int] = Field(None, ge=1, description="Pixel width if known")
    height: Optional[int] = Field(None, ge=1, description="Pixel height if known")
    format: Optional[str] = Field(None, description="Image format (PNG, JPEG, WEBP, TIFF)")
    dpi: Optional[int] = Field(None, ge=1, description="Image resolution DPI if known")


class FigureResult(BaseModel):
    """
    Structured outcome of figure/image analysis and caption association.
    """
    figure_id: str = Field(..., description="Unique figure identifier")
    page_index: int = Field(0, ge=0, description="0-indexed document page index")
    bbox: BoundingBox = Field(..., description="Normalized bounding box [left, top, right, bottom]")
    polygon: Optional[List[Point2D]] = Field(None, description="Optional contour polygon points")
    figure_type: FigureType = Field(FigureType.FIGURE, description="Classified figure category")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Classification/detection confidence score")
    description: Optional[str] = Field(None, description="Optional text description or caption summary")
    associated_caption_id: Optional[str] = Field(None, description="ID of associated caption block")
    associated_caption_text: Optional[str] = Field(None, description="Text of associated caption")
    provider_id: str = Field(..., description="Provider ID (e.g. 'local_figure_analyzer')")
    model_id: str = Field(..., description="Model ID (e.g. 'BasicFigureAnalyzer-v1')")
    processing_time_ms: float = Field(0.0, ge=0.0, description="Inference latency in ms")
    provenance: Optional[Provenance] = Field(None, description="Provenance metadata")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Image metadata (dimensions, format, aspect_ratio)")

    @field_validator("confidence")
    @classmethod
    def validate_confidence_bounds(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError(f"Figure confidence ({v}) must be between 0.0 and 1.0")
        return round(v, 4)
