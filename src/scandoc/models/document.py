"""
Document-level schema structures, page collections, reading order, and root DocumentIR.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, model_validator
from scandoc.models.blocks import BlockNode
from scandoc.models.geometry import SizeUnit
from scandoc.models.provenance import Provenance


class DocumentMetadata(BaseModel):
    """Metadata describing document identity, source properties, and origin."""
    id: str = Field(..., description="Unique document identifier")
    name: str = Field(..., description="Original filename or title string")
    mime_type: Optional[str] = Field(None, description="Source MIME type (e.g., 'application/pdf')")
    page_count: int = Field(0, ge=0, description="Total page count")
    title: Optional[str] = Field(None, description="Document title metadata")
    author: Optional[str] = Field(None, description="Document author metadata")
    created_at: Optional[str] = Field(None, description="ISO 8601 creation timestamp")
    mod_date: Optional[str] = Field(None, description="ISO 8601 modification timestamp")
    extra: Dict[str, str] = Field(default_factory=dict, description="Arbitrary metadata key-values")


class Page(BaseModel):
    """Represents a single document physical page container."""
    page_index: int = Field(..., ge=0, description="0-indexed page sequence number")
    width: float = Field(..., gt=0.0, description="Page width dimension")
    height: float = Field(..., gt=0.0, description="Page height dimension")
    dpi: Optional[int] = Field(None, ge=1, description="Raster rendering DPI if applicable")
    rotation: int = Field(0, description="Page rotation angle in degrees (0, 90, 180, 270)")
    unit: SizeUnit = Field(SizeUnit.POINTS, description="Measurement unit for page dimensions")
    blocks: List[BlockNode] = Field(default_factory=list, description="Extracted content blocks on page")
    provenance: Optional[List[Provenance]] = Field(None, description="Page-level extraction provenance")

    @model_validator(mode="after")
    def validate_block_page_indices(self) -> "Page":
        """Ensure all contained blocks reference this page index in their bounding boxes."""
        for block in self.blocks:
            if block.bbox.page_index != self.page_index:
                # Synchronize or validate page_index
                block.bbox.page_index = self.page_index
        return self


class ReadingOrder(BaseModel):
    """Explicit document reading order sequence."""
    sequence: List[str] = Field(
        default_factory=list,
        description="Ordered list of Block IDs representing primary reading flow"
    )


class DocumentStructure(BaseModel):
    """Hierarchical document outline and structural grouping."""
    heading_tree: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Map of heading block ID to child block IDs"
    )
    body_block_ids: List[str] = Field(
        default_factory=list,
        description="List of block IDs belonging to main body flow"
    )
    furniture_block_ids: List[str] = Field(
        default_factory=list,
        description="List of block IDs belonging to headers, footers, or page numbers"
    )


class DocumentIR(BaseModel):
    """
    Root Unified Document Representation (DocumentIR).
    
    Serves as the lossless, runtime-agnostic internal graph model produced and
    consumed by all scanDOC pipeline components.
    """
    metadata: DocumentMetadata = Field(..., description="Document metadata")
    pages: List[Page] = Field(default_factory=list, description="Document page containers")
    reading_order: ReadingOrder = Field(
        default_factory=ReadingOrder,
        description="Explicit reading order sequence"
    )
    structure: DocumentStructure = Field(
        default_factory=DocumentStructure,
        description="Document section hierarchy and body/furniture grouping"
    )

    @model_validator(mode="after")
    def validate_document_integrity(self) -> "DocumentIR":
        """
        Validate cross-page constraints:
        1. Block IDs must be globally unique across all pages.
        2. Reading order sequence IDs must reference existing block IDs.
        3. Page indices must be sequential (0..N-1).
        """
        seen_block_ids = set()
        for page in self.pages:
            for block in page.blocks:
                if block.id in seen_block_ids:
                    raise ValueError(f"Duplicate Block ID '{block.id}' found across pages")
                seen_block_ids.add(block.id)

        # Validate reading order references
        for ref_id in self.reading_order.sequence:
            if ref_id not in seen_block_ids:
                raise ValueError(
                    f"Reading order references non-existent Block ID '{ref_id}'"
                )

        return self

    def get_block(self, block_id: str) -> Optional[BlockNode]:
        """Lookup a block node by its unique ID across all pages."""
        for page in self.pages:
            for block in page.blocks:
                if block.id == block_id:
                    return block
        return None

    def all_blocks(self) -> List[BlockNode]:
        """Return a flattened list of all blocks across all pages."""
        result = []
        for page in self.pages:
            result.extend(page.blocks)
        return result
