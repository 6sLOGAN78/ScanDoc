"""
Pydantic data models for table structure, cell, row, column, and configuration.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from scandoc.models.geometry import BoundingBox, Point2D
from scandoc.models.provenance import Provenance


class TableStructureConfig(BaseModel):
    """
    Configuration model for table structure recognition providers.
    """
    model_name: str = Field("SLANet-DocTable", description="Target table model identifier")
    model_path: Optional[str] = Field(None, description="Path to local ONNX model weights")
    confidence_threshold: float = Field(0.5, ge=0.0, le=1.0, description="Minimum detection confidence threshold")
    device: str = Field("auto", description="Execution device ('cpu', 'cuda', 'auto')")
    batch_size: int = Field(1, ge=1, description="Batch size for inference")
    extra_options: Dict[str, str] = Field(default_factory=dict, description="Provider-specific options")


class TableCellStructure(BaseModel):
    """
    Individual table cell representation with rowspan, colspan, and geometry.
    """
    cell_id: str = Field(..., description="Unique cell identifier")
    row_index: int = Field(..., ge=0, description="0-indexed starting row position")
    col_index: int = Field(..., ge=0, description="0-indexed starting column position")
    row_span: int = Field(1, ge=1, description="Row span count for merged cells")
    col_span: int = Field(1, ge=1, description="Column span count for merged cells")
    bbox: BoundingBox = Field(..., description="Normalized bounding box [left, top, right, bottom]")
    polygon: Optional[List[Point2D]] = Field(None, description="Optional polygon contour points")
    text: str = Field("", description="Assigned text content")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Cell detection confidence")
    is_header: bool = Field(False, description="True if cell is classified as header")
    provenance: Optional[Provenance] = Field(None, description="Provenance metadata for cell structure")

    @field_validator("confidence")
    @classmethod
    def validate_confidence_bounds(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError(f"Cell confidence ({v}) must be between 0.0 and 1.0")
        return round(v, 4)


class TableRowStructure(BaseModel):
    """
    Row metadata container.
    """
    row_index: int = Field(..., ge=0, description="0-indexed row position")
    bbox: Optional[BoundingBox] = Field(None, description="Bounding box covering whole row")
    is_header: bool = Field(False, description="True if row is a header row")


class TableColumnStructure(BaseModel):
    """
    Column metadata container.
    """
    col_index: int = Field(..., ge=0, description="0-indexed column position")
    bbox: Optional[BoundingBox] = Field(None, description="Bounding box covering whole column")


class TableStructureResult(BaseModel):
    """
    Complete structured representation of a recognized table.
    """
    table_id: str = Field(..., description="Unique table identifier")
    page_index: int = Field(0, ge=0, description="0-indexed document page index")
    bbox: BoundingBox = Field(..., description="Normalized bounding box of table boundary")
    num_rows: int = Field(..., ge=1, description="Total row count")
    num_cols: int = Field(..., ge=1, description="Total column count")
    rows: List[TableRowStructure] = Field(default_factory=list, description="Table row metadata")
    cols: List[TableColumnStructure] = Field(default_factory=list, description="Table column metadata")
    cells: List[TableCellStructure] = Field(default_factory=list, description="Grid cells with row/col spans")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Overall table structure confidence")
    provider_id: str = Field(..., description="Table provider ID (e.g. 'slanet_table')")
    model_id: str = Field(..., description="Model identifier (e.g. 'SLANet-v1')")
    processing_time_ms: float = Field(0.0, ge=0.0, description="Inference latency in ms")
    provenance: Optional[Provenance] = Field(None, description="Provenance metadata for table recognition")
