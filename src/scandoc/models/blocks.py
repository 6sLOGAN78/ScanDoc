"""
Typed block primitives and document node types for scanDOC DocumentIR.
"""

from enum import Enum
from typing import Annotated, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator
from scandoc.models.geometry import BoundingBox, Point2D
from scandoc.models.provenance import Provenance


class BlockType(str, Enum):
    """Enumeration of recognized document block types."""
    TEXT = "text"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    TABLE = "table"
    FIGURE = "figure"
    FORMULA = "formula"
    CAPTION = "caption"


class TextSpan(BaseModel):
    """Granular character or word-level text span with spatial bounds."""
    text: str = Field(..., description="Sub-text string")
    start_char_idx: int = Field(..., ge=0, description="Start character offset")
    end_char_idx: int = Field(..., ge=0, description="End character offset")
    bbox: Optional[BoundingBox] = Field(None, description="Spatial bounds for span")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="OCR/text confidence")


class BaseBlock(BaseModel):
    """Abstract base class for all DocumentIR blocks."""
    id: str = Field(..., description="Unique block node identifier")
    bbox: BoundingBox = Field(..., description="Spatial bounding box")
    polygon: Optional[List[Point2D]] = Field(None, description="Optional bounding polygon contour")
    reading_order_index: int = Field(0, ge=0, description="Explicit 0-indexed reading order position")
    provenance: Optional[Provenance] = Field(None, description="Extraction provenance metadata")


class TextBlock(BaseBlock):
    """Represents a basic text block or line."""
    block_type: Literal[BlockType.TEXT] = BlockType.TEXT
    text: str = Field(..., description="Raw extracted text string")
    spans: Optional[List[TextSpan]] = Field(None, description="Detailed character/word spans")


class HeadingBlock(BaseBlock):
    """Represents a document section heading (H1 - H6)."""
    block_type: Literal[BlockType.HEADING] = BlockType.HEADING
    text: str = Field(..., description="Heading title text")
    level: int = Field(1, ge=1, le=6, description="Heading level from 1 (main title) to 6 (sub-heading)")


class ParagraphBlock(BaseBlock):
    """Represents a multi-line paragraph block."""
    block_type: Literal[BlockType.PARAGRAPH] = BlockType.PARAGRAPH
    text: str = Field(..., description="Combined paragraph text")
    child_text_ids: Optional[List[str]] = Field(None, description="Optional IDs of contained TextBlocks")


class ListItem(BaseModel):
    """Individual item within a ListBlock."""
    text: str = Field(..., description="List item text")
    marker: Optional[str] = Field(None, description="Bullet marker or number string (e.g. '1.', '•')")
    reading_order_index: int = Field(0, ge=0, description="Order index within item list")
    bbox: Optional[BoundingBox] = Field(None, description="Item spatial bounding box")


class ListBlock(BaseBlock):
    """Represents an ordered or unordered bulleted list block."""
    block_type: Literal[BlockType.LIST] = BlockType.LIST
    ordered: bool = Field(False, description="True if numbered/ordered list, False if bulleted")
    items: List[ListItem] = Field(default_factory=list, description="List of contained items")


class TableCell(BaseModel):
    """Individual grid cell within a TableBlock."""
    cell_id: str = Field(..., description="Unique cell identifier")
    row_index: int = Field(..., ge=0, description="0-indexed row position")
    col_index: int = Field(..., ge=0, description="0-indexed column position")
    row_span: int = Field(1, ge=1, description="Number of rows spanned by this cell")
    col_span: int = Field(1, ge=1, description="Number of columns spanned by this cell")
    is_header: bool = Field(False, description="True if this cell is a column or row header")
    text: str = Field("", description="Textual content of the cell")
    bbox: Optional[BoundingBox] = Field(None, description="Cell bounding box")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Structure/text confidence score")


class TableBlock(BaseBlock):
    """Represents a structured table grid with row/col spans."""
    block_type: Literal[BlockType.TABLE] = BlockType.TABLE
    num_rows: int = Field(..., ge=1, description="Total number of table rows")
    num_cols: int = Field(..., ge=1, description="Total number of table columns")
    cells: List[TableCell] = Field(default_factory=list, description="List of table grid cells")
    caption: Optional[str] = Field(None, description="Table title or caption text")

    @field_validator("cells")
    @classmethod
    def validate_cells_fit_grid(cls, cells: List[TableCell], info) -> List[TableCell]:
        """Ensure cells do not exceed specified grid dimensions."""
        num_rows = info.data.get("num_rows")
        num_cols = info.data.get("num_cols")
        if num_rows is not None and num_cols is not None:
            for cell in cells:
                if cell.row_index >= num_rows:
                    raise ValueError(
                        f"Cell row_index ({cell.row_index}) exceeds table num_rows ({num_rows})"
                    )
                if cell.col_index >= num_cols:
                    raise ValueError(
                        f"Cell col_index ({cell.col_index}) exceeds table num_cols ({num_cols})"
                    )
        return cells


class ImageRef(BaseModel):
    """
    Representation of raster/vector figure assets without requiring heavy PIL or OpenCV
    dependencies inside core IR.
    """
    uri: Optional[str] = Field(None, description="Resource URI")
    path: Optional[str] = Field(None, description="Local disk filepath")
    mime_type: Optional[str] = Field(None, description="MIME type (e.g. 'image/png', 'image/jpeg')")
    base64_data: Optional[str] = Field(None, description="Base64 encoded image string")
    width_px: Optional[int] = Field(None, ge=1, description="Image pixel width")
    height_px: Optional[int] = Field(None, ge=1, description="Image pixel height")
    size_bytes: Optional[int] = Field(None, ge=0, description="Image binary size in bytes")


class FigureBlock(BaseBlock):
    """Represents an image, diagram, chart, or visual figure block."""
    block_type: Literal[BlockType.FIGURE] = BlockType.FIGURE
    caption: Optional[str] = Field(None, description="Figure caption text")
    alt_text: Optional[str] = Field(None, description="Accessible alt text description")
    image_ref: Optional[ImageRef] = Field(None, description="Asset reference")


class FormulaFormat(str, Enum):
    """Representation format for mathematical formulas."""
    LATEX = "LATEX"
    MATHML = "MATHML"
    ASCII = "ASCII"
    TEXT = "TEXT"


class FormulaBlock(BaseBlock):
    """Represents inline or block mathematical equations."""
    block_type: Literal[BlockType.FORMULA] = BlockType.FORMULA
    expression: str = Field(..., description="Mathematical formula expression string")
    format: FormulaFormat = Field(FormulaFormat.LATEX, description="Formula notation format")
    is_inline: bool = Field(False, description="True if inline math, False if block math")


class CaptionBlock(BaseBlock):
    """Represents a standalone table or figure caption block."""
    block_type: Literal[BlockType.CAPTION] = BlockType.CAPTION
    text: str = Field(..., description="Caption text string")
    target_block_id: Optional[str] = Field(None, description="ID of figure or table being captioned")


# Discriminated Union for Pydantic polymorphic block deserialization
BlockNode = Annotated[
    Union[
        TextBlock,
        HeadingBlock,
        ParagraphBlock,
        ListBlock,
        TableBlock,
        FigureBlock,
        FormulaBlock,
        CaptionBlock,
    ],
    Field(discriminator="block_type"),
]
