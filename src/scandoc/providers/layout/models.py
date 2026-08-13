"""
Data models for layout region detection, layout config, and layout result.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from scandoc.models.geometry import BoundingBox, Point2D
from scandoc.providers.layout.taxonomy import LayoutCategory


class LayoutConfig(BaseModel):
    """
    Configuration model for document layout analysis.
    """
    model_name: str = Field("RT-DETR-DocLayNet", description="Target layout model identifier")
    model_path: Optional[str] = Field(None, description="Path to local ONNX model file")
    confidence_threshold: float = Field(0.5, ge=0.0, le=1.0, description="Minimum detection confidence threshold")
    iou_threshold: float = Field(0.5, ge=0.0, le=1.0, description="NMS IoU overlap threshold")
    device: str = Field("auto", description="Execution device identifier ('cpu', 'cuda', 'auto')")
    batch_size: int = Field(1, ge=1, description="Batch size for layout inference")
    class_taxonomy: str = Field("doclaynet", description="Dataset taxonomy mapper name ('doclaynet', 'publaynet')")
    extra_options: Dict[str, str] = Field(default_factory=dict, description="Provider-specific configuration key-values")


class LayoutRegion(BaseModel):
    """
    Individual visual layout region detected on a document page.
    """
    category: LayoutCategory = Field(..., description="Standardized layout region category")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection model confidence score (0.0 to 1.0)")
    bbox: BoundingBox = Field(..., description="Normalized top-left origin bounding box [left, top, right, bottom]")
    polygon: Optional[List[Point2D]] = Field(None, description="Optional multi-point contour polygon")
    page_index: int = Field(0, ge=0, description="Target document page index")
    raw_class_id: Optional[str] = Field(None, description="Raw model class ID string or integer")
    raw_class_name: Optional[str] = Field(None, description="Raw dataset class label string")
    region_idx: int = Field(0, ge=0, description="0-indexed detection order sequence")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Model inference metadata")

    @field_validator("confidence")
    @classmethod
    def validate_confidence_bounds(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError(f"Layout region confidence ({v}) must be between 0.0 and 1.0")
        return round(v, 4)


class LayoutResult(BaseModel):
    """
    Structured outcome of layout analysis over a document page.
    """
    regions: List[LayoutRegion] = Field(default_factory=list, description="List of detected visual layout regions")
    provider_id: str = Field(..., description="Identifier of layout provider (e.g. 'rt_detr_layout')")
    model_id: str = Field(..., description="Model checkpoint identifier (e.g. 'RT-DETR-DocLayNet')")
    image_width: int = Field(..., ge=1, description="Pixel width of target page image")
    image_height: int = Field(..., ge=1, description="Pixel height of target page image")
    page_index: int = Field(0, ge=0, description="Target document page index")
    processing_time_ms: float = Field(0.0, ge=0.0, description="Inference latency in milliseconds")
