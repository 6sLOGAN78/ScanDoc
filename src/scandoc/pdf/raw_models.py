"""
Raw PDF extraction intermediate data models.

Serves as an internal data transfer boundary between backend PDF libraries
(e.g., pypdfium2) and the DocumentIR assembler.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class RawPdfTextSpan(BaseModel):
    """Raw text span or glyph run extracted from a PDF content stream."""
    text: str = Field(..., description="Text content")
    bbox_pdf: tuple[float, float, float, float] = Field(
        ...,
        description="Raw PDF bounding box (left, bottom, right, top) in PDF points"
    )
    font_name: Optional[str] = Field(None, description="Font name if available")
    font_size: Optional[float] = Field(None, description="Font size in points if available")
    char_start: int = Field(0, ge=0, description="Start character offset")
    char_end: int = Field(0, ge=0, description="End character offset")


class RawPdfTextBlock(BaseModel):
    """Raw text block or line sequence from PDF content stream."""
    text: str = Field(..., description="Combined text string")
    bbox_pdf: tuple[float, float, float, float] = Field(
        ...,
        description="Raw PDF bounding box (left, bottom, right, top) in PDF points"
    )
    spans: List[RawPdfTextSpan] = Field(default_factory=list, description="Child text spans")
    reading_sequence_idx: int = Field(0, ge=0, description="Natural stream position index")


class RawPdfImage(BaseModel):
    """Raw embedded image object metadata from PDF page."""
    image_index: int = Field(..., ge=0, description="0-indexed image index on page")
    bbox_pdf: tuple[float, float, float, float] = Field(
        ...,
        description="Raw PDF bounding box (left, bottom, right, top) in PDF points"
    )
    width_px: int = Field(..., ge=1, description="Pixel width of raster asset")
    height_px: int = Field(..., ge=1, description="Pixel height of raster asset")
    mime_type: Optional[str] = Field(None, description="MIME type if identifiable")


class RawPdfLink(BaseModel):
    """Raw annotation link or URI target from PDF page."""
    uri: Optional[str] = Field(None, description="Target URI if web link")
    target_page: Optional[int] = Field(None, ge=0, description="Target 0-indexed page number if internal link")
    bbox_pdf: tuple[float, float, float, float] = Field(
        ...,
        description="Raw PDF bounding box (left, bottom, right, top) in PDF points"
    )


class RawPdfPageData(BaseModel):
    """Raw extracted page elements for a single PDF page."""
    page_index: int = Field(..., ge=0, description="0-indexed page index")
    width: float = Field(..., gt=0.0, description="Page physical width in points")
    height: float = Field(..., gt=0.0, description="Page physical height in points")
    rotation: int = Field(0, description="Page rotation in degrees (0, 90, 180, 270)")
    text_blocks: List[RawPdfTextBlock] = Field(default_factory=list, description="Extracted raw text blocks")
    images: List[RawPdfImage] = Field(default_factory=list, description="Extracted raw image objects")
    links: List[RawPdfLink] = Field(default_factory=list, description="Extracted links / annotations")


class RawPdfMetadata(BaseModel):
    """Raw document-level metadata extracted from PDF catalog."""
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    creation_date: Optional[str] = None
    mod_date: Optional[str] = None
    page_count: int = 0
    extra: Dict[str, str] = Field(default_factory=dict)
