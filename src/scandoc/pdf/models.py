"""
Pydantic data models and schemas for PDF inspection results.
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from scandoc.models.geometry import BoundingBox, SizeUnit


class PageContentType(str, Enum):
    """Classification of content types present on an individual PDF page."""
    DIGITAL_TEXT_ONLY = "DIGITAL_TEXT_ONLY"
    SCANNED_IMAGE_ONLY = "SCANNED_IMAGE_ONLY"
    HYBRID = "HYBRID"
    EMPTY = "EMPTY"


class DocumentCategory(str, Enum):
    """Overall classification of document generation source."""
    DIGITALLY_GENERATED = "DIGITALLY_GENERATED"
    SCANNED = "SCANNED"
    HYBRID = "HYBRID"
    IMAGE_ONLY = "IMAGE_ONLY"


class ImageDetails(BaseModel):
    """Characteristics and spatial metrics of an embedded image object."""
    image_index: int = Field(..., ge=0, description="0-indexed image index on page")
    width_px: int = Field(..., ge=1, description="Pixel width of image asset")
    height_px: int = Field(..., ge=1, description="Pixel height of image asset")
    horizontal_dpi: Optional[float] = Field(None, description="Calculated horizontal DPI")
    vertical_dpi: Optional[float] = Field(None, description="Calculated vertical DPI")
    page_coverage_ratio: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Fraction of total page area covered by this image"
    )
    bbox: Optional[BoundingBox] = Field(None, description="Spatial bounding box on page")


class PageInspectionResult(BaseModel):
    """Inspection metrics for a single PDF page."""
    page_index: int = Field(..., ge=0, description="0-indexed page sequence number")
    width: float = Field(..., gt=0.0, description="Page physical width")
    height: float = Field(..., gt=0.0, description="Page physical height")
    rotation: int = Field(0, description="Page rotation angle in degrees (0, 90, 180, 270)")
    unit: SizeUnit = Field(SizeUnit.POINTS, description="Measurement unit for page dimensions")
    content_type: PageContentType = Field(..., description="Detected page content composition")
    character_count: int = Field(0, ge=0, description="Count of native text characters")
    word_count: int = Field(0, ge=0, description="Count of native text words")
    text_density_ratio: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Estimated text density relative to page capacity"
    )
    has_native_text: bool = Field(False, description="True if native text vector stream exists")
    has_images: bool = Field(False, description="True if raster images exist on page")
    image_count: int = Field(0, ge=0, description="Number of embedded image objects")
    images: List[ImageDetails] = Field(default_factory=list, description="Details of embedded images")
    image_coverage_ratio: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Combined area coverage of all images relative to page size"
    )


class PipelineSignals(BaseModel):
    """Downstream pipeline decision signals produced by inspection."""
    recommended_fast_path: bool = Field(
        False,
        description="True if digital PDF can skip heavy ML models and execute via fast native vector path"
    )
    has_native_text: bool = Field(False, description="True if document contains usable native text")
    ocr_suggested: bool = Field(False, description="True if OCR is recommended for scanned or hybrid pages")
    vlm_suggested: bool = Field(False, description="True if VLM is recommended for complex image-only pages")
    is_encrypted: bool = Field(False, description="True if document is password protected")
    avg_text_density: float = Field(0.0, ge=0.0, le=1.0, description="Average page text density across document")
    scanned_page_ratio: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Fraction of pages classified as scanned or image-only"
    )


class PdfInspectionResult(BaseModel):
    """Root structured output produced by PDFInspector."""
    file_path: Optional[str] = Field(None, description="Input file path if loaded from disk")
    file_size_bytes: int = Field(0, ge=0, description="Input file size in bytes")
    page_count: int = Field(0, ge=0, description="Total number of pages")
    title: Optional[str] = Field(None, description="PDF Title metadata entry")
    author: Optional[str] = Field(None, description="PDF Author metadata entry")
    subject: Optional[str] = Field(None, description="PDF Subject metadata entry")
    creator: Optional[str] = Field(None, description="PDF Creator application metadata entry")
    producer: Optional[str] = Field(None, description="PDF Producer library metadata entry")
    creation_date: Optional[str] = Field(None, description="Creation date string")
    mod_date: Optional[str] = Field(None, description="Modification date string")
    is_encrypted: bool = Field(False, description="Encryption state")
    category: DocumentCategory = Field(..., description="Overall document classification")
    pages: List[PageInspectionResult] = Field(default_factory=list, description="Per-page inspection results")
    signals: PipelineSignals = Field(..., description="Downstream execution pipeline signals")
    extra_metadata: Dict[str, str] = Field(default_factory=dict, description="Additional PDF metadata key-values")
